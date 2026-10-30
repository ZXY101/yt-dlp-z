import { useState } from "react";

interface SuggestionListOptions {
  value: string;
  suggestions: string[];
  onPick: (suggestion: string) => void;
}

/** Keyboard and open/closed state for a text field with a suggestion dropdown
 * (the ARIA combobox pattern). The field keeps focus; `active` is the highlighted row. */
export function useSuggestionList({ value, suggestions, onPick }: SuggestionListOptions) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const typed = value.toLowerCase();
  const matches = suggestions.filter(
    (item) => item.toLowerCase().startsWith(typed) && item.toLowerCase() !== typed,
  );
  const visible = open && matches.length > 0;

  function pick(suggestion: string) {
    onPick(suggestion);
    setActive(-1);
  }

  function move(step: number) {
    setOpen(true);
    setActive((current) => (current + step + matches.length) % matches.length);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      move(event.key === "ArrowDown" ? 1 : -1);
      return;
    }
    if (event.key === "Escape" && visible) {
      event.preventDefault();
      setOpen(false);
      return;
    }
    if (event.key === "Enter" && visible && matches[active] !== undefined) {
      event.preventDefault();
      pick(matches[active]);
    }
  }

  return {
    matches,
    visible,
    active: visible ? active : -1,
    pick,
    open: () => setOpen(true),
    close: () => setOpen(false),
    reset: () => setActive(-1),
    handleKeyDown,
  };
}
