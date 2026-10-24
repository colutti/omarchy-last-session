"""Recover dwindle's visible binary partition from saved window rectangles.

No compositor internals or persistent window rules: build the partition with
preselect and then resize tiles using Hyprland's public Lua dispatchers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from omarchy_last_session import hypr, warn
from omarchy_last_session.restore import placement
from omarchy_last_session.restore.pairing import Pairing
from omarchy_last_session.session import SavedWindow


@dataclass
class Leaf:
    window: SavedWindow
    address: str


@dataclass
class Split:
    axis: str
    ratio: float
    first: Tree
    second: Tree


Tree = Union[Leaf, Split]


def leaves(tree: Tree) -> list[Leaf]:
    if isinstance(tree, Leaf):
        return [tree]
    return leaves(tree.first) + leaves(tree.second)


def infer_tree(seats: list[Pairing]) -> Tree | None:
    if not seats:
        return None
    if len(seats) == 1:
        return Leaf(*seats[0])
    for axis, direction in ((0, "r"), (1, "d")):
        ordered = sorted(seats, key=lambda seat: seat[0]["at"][axis])
        for cut in range(1, len(ordered)):
            left, right = ordered[:cut], ordered[cut:]
            end = max(w["at"][axis] + w["size"][axis] for w, _ in left)
            start = min(w["at"][axis] for w, _ in right)
            if end > start:
                continue
            first, second = infer_tree(left), infer_tree(right)
            if first is None or second is None:
                continue
            lo = min(w["at"][axis] for w, _ in seats)
            hi = max(w["at"][axis] + w["size"][axis] for w, _ in seats)
            gap = start - end
            span = hi - lo + gap
            if span <= 0:
                continue
            ratio = 2 * (end - lo + gap) / span
            return Split(direction, max(0.1, min(1.9, ratio)), first, second)
    return None


def build_commands(tree: Tree) -> str:
    tiles = leaves(tree)
    commands = []

    def dispatch(body: str) -> None:
        commands.append(f"hl.dispatch({body})")

    for tile in tiles:
        target = hypr.quote_window(tile.address)
        dispatch(f"hl.dsp.window.fullscreen({{ mode = 'fullscreen', action = 'unset', window = {target} }})")
        dispatch(f"hl.dsp.window.fullscreen({{ mode = 'maximized', action = 'unset', window = {target} }})")
        dispatch(f"hl.dsp.window.float({{ action = 'on', window = {target} }})")
    dispatch(f"hl.dsp.window.float({{ action = 'off', window = {hypr.quote_window(tiles[0].address)} }})")

    def split(node: Tree) -> None:
        if isinstance(node, Leaf):
            return
        anchor = hypr.quote_window(leaves(node.first)[0].address)
        incoming = hypr.quote_window(leaves(node.second)[0].address)
        dispatch(f"hl.dsp.focus({{ window = {anchor} }})")
        dispatch(f"hl.dsp.layout('preselect {node.axis}')")
        dispatch(f"hl.dsp.window.float({{ action = 'off', window = {incoming} }})")
        dispatch(f"hl.dsp.focus({{ window = {anchor} }})")
        dispatch(f"hl.dsp.layout('splitratio {node.ratio:.6f} exact')")
        split(node.first)
        split(node.second)

    split(tree)
    # Absolute client sizes remove the gap/border approximation from inferred ratios.
    for tile in tiles:
        width, height = tile.window["size"]
        target = hypr.quote_window(tile.address)
        dispatch(f"hl.dsp.window.resize({{ x = {width}, y = {height}, window = {target} }})")
    dispatch("hl.dsp.layout('preselect none')")
    return "; ".join(commands)


def restore_tiled_geometry(placed: list[Pairing]) -> None:
    live = hypr.get_managed_clients()
    by_workspace: dict[str, list[Pairing]] = {}
    for win, address in placed:
        if not win["floating"]:
            by_workspace.setdefault(hypr.format_workspace_selector(win["workspace"]), []).append(
                (win, address)
            )
    for selector, seats in by_workspace.items():
        if len(seats) < 2:
            continue
        # Fullscreen and grouped rectangles hide the original partition. Never
        # guess a tree from them or remove a new/unpaired window from its layout.
        if any(w.get("group") is not None or w.get("fullscreen") for w, _ in seats):
            warn(f"workspace {selector}: grouped/fullscreen tiles retain the default layout")
            continue
        addresses = {address for _, address in seats}
        extra = [
            c
            for a, c in live.items()
            if hypr.format_workspace_selector(c["workspace"]) == selector
            and not c.get("floating")
            and a not in addresses
        ]
        if extra:
            warn(f"workspace {selector}: unpaired tiles present, preserving live layout")
            continue
        # Per-workspace layout can differ from general:layout.
        code = f"local w = hl.get_workspace({hypr.quote_lua(selector)}) return w and w.tiled_layout or ''"
        if hypr._request("repl", code).strip() != "dwindle":
            warn(f"workspace {selector}: exact geometry currently supports dwindle only")
            continue
        tree = infer_tree(seats)
        if tree is None:
            warn(f"workspace {selector}: rectangles do not form a binary partition")
            continue
        if not hypr.eval_lua(build_commands(tree)):
            warn(f"workspace {selector}: tile reconstruction was rejected")
        for win, address in seats:
            placement.apply_fullscreen(win, hypr.quote_window(address))
