import { useState } from "react";

import type {
  NotificationSettings,
  NotificationSettingsIn,
  NotifyEvent,
} from "@/features/settings/types";

// ntfy's own rule for topic names.
const TOPIC_PATTERN = /^[-_A-Za-z0-9]{0,64}$/;

function topicError(topic: string) {
  return TOPIC_PATTERN.test(topic)
    ? undefined
    : "Use up to 64 letters, digits, - and _ (no spaces).";
}

export function useNotificationForm(saved: NotificationSettings) {
  const [server, setServer] = useState(saved.server);
  const [topic, setTopic] = useState(saved.topic);
  const [token, setToken] = useState("");
  const [removeToken, setRemoveToken] = useState(false);
  const [events, setEvents] = useState<NotifyEvent[]>(saved.events);
  const [checked, setChecked] = useState(false);
  const error = checked ? topicError(topic.trim()) : undefined;

  function toggleEvent(event: NotifyEvent, on: boolean) {
    setEvents((current) => (on ? [...current, event] : current.filter((e) => e !== event)));
  }

  function tokenValue() {
    if (token.trim()) {
      return token.trim();
    }
    // null keeps the saved token.
    return removeToken ? "" : null;
  }

  /** The settings to send, or null when the topic isn't valid. */
  function request(): NotificationSettingsIn | null {
    setChecked(true);
    if (topicError(topic.trim())) {
      return null;
    }
    return { server: server.trim(), topic: topic.trim(), token: tokenValue(), events };
  }

  /** After saving: the saved token isn't shown again. */
  function clearToken() {
    setToken("");
    setRemoveToken(false);
  }

  return {
    fields: { server, setServer, topic, setTopic, token, setToken, events, toggleEvent },
    removeToken,
    setRemoveToken,
    topicError: error,
    request,
    clearToken,
  };
}

export type NotificationForm = ReturnType<typeof useNotificationForm>;
