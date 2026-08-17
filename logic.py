"""Application logic for clipboard history management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import tkinter as tk


@dataclass
class ClipboardEntry:
	text: str
	pinned: bool = False


@dataclass
class ClipboardHistoryManager:
	"""Track unique clipboard text in most-recent-first order."""

	max_items: int = 50
	storage_path: Path = field(
		default_factory=lambda: Path(__file__).resolve().parent / "clipboard_history.json"
	)
	_history: List[ClipboardEntry] = field(default_factory=list)
	_last_seen: Optional[str] = None

	def __post_init__(self) -> None:
		self._load_from_disk()

	def poll_system_clipboard(self, root: tk.Misc) -> bool:
		"""Read the current clipboard text and store it if it changed."""

		try:
			current_text = root.clipboard_get()
		except tk.TclError:
			return False

		return self.add_item(current_text)

	def add_item(self, text: str) -> bool:
		"""Add a new clipboard item if it is not the same as the last item seen."""
		text = text.strip()
		if not text:
			return False

		if text == self._last_seen:
			return False

		existing_index = self._find_index_by_text(text)
		pinned = False
		if existing_index is not None:
			pinned = self._history.pop(existing_index).pinned

		self._last_seen = text
		self._history.insert(0, ClipboardEntry(text=text, pinned=pinned))
		self._normalize_order()
		if len(self._history) > self.max_items:
			self._history = self._history[: self.max_items]
		self._save_to_disk()
		return True

	def get_history(self) -> List[ClipboardEntry]:
		return list(self._history)

	def get_item(self, index: int) -> ClipboardEntry:
		return self._history[index]

	def get_filtered_indices(self, query: str = "") -> List[int]:
		normalized_query = query.strip().lower()
		if not normalized_query:
			return list(range(len(self._history)))

		matching_indices: List[int] = []
		for index, item in enumerate(self._history):
			if normalized_query in item.text.lower():
				matching_indices.append(index)
		return matching_indices

	def delete_item(self, index: int) -> None:
		del self._history[index]
		self._save_to_disk()

	def toggle_pinned(self, index: int) -> bool:
		entry = self._history[index]
		entry.pinned = not entry.pinned
		self._normalize_order()
		self._save_to_disk()
		return entry.pinned

	def clear(self) -> None:
		self._history.clear()
		self._last_seen = None
		self._save_to_disk()

	def _normalize_order(self) -> None:
		pinned_entries = [entry for entry in self._history if entry.pinned]
		regular_entries = [entry for entry in self._history if not entry.pinned]
		self._history = pinned_entries + regular_entries

	def _find_index_by_text(self, text: str) -> Optional[int]:
		for index, entry in enumerate(self._history):
			if entry.text == text:
				return index
		return None

	def _load_from_disk(self) -> None:
		if not self.storage_path.exists():
			return

		try:
			items = json.loads(self.storage_path.read_text(encoding="utf-8"))
		except (json.JSONDecodeError, OSError):
			return

		if not isinstance(items, list):
			return

		loaded_entries: List[ClipboardEntry] = []
		for item in items:
			if not isinstance(item, dict):
				continue
			text = item.get("text", "")
			pinned = bool(item.get("pinned", False))
			if isinstance(text, str) and text.strip():
				loaded_entries.append(ClipboardEntry(text=text, pinned=pinned))

		self._history = loaded_entries[: self.max_items]
		self._normalize_order()
		if self._history:
			self._last_seen = self._history[0].text

	def _save_to_disk(self) -> None:
		payload = [{"text": entry.text, "pinned": entry.pinned} for entry in self._history]
		try:
			self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
		except OSError:
			# Do not crash the app if disk writes fail.
			pass

