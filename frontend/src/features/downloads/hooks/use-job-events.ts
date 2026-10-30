import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { JOBS_KEY, applyJobEvent } from "@/features/downloads/jobs";
import type { JobEvent } from "@/features/downloads/types";

const UNAUTHORIZED_CLOSE_CODE = 4401;
const FIRST_RETRY_MS = 500;
const MAX_RETRY_MS = 10_000;

function eventsUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/ws`;
}

function retryDelay(attempt: number) {
  return Math.min(MAX_RETRY_MS, FIRST_RETRY_MS * 2 ** attempt);
}

/** Keeps the job list live over /api/ws, reconnecting with backoff when the socket drops. */
export function useJobEvents() {
  const queryClient = useQueryClient();

  useEffect(() => {
    let socket: WebSocket | undefined;
    let attempt = 0;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let stopped = false;

    function handleClose(event: CloseEvent) {
      if (stopped) {
        return;
      }
      if (event.code === UNAUTHORIZED_CLOSE_CODE) {
        // Signed out elsewhere: refetching the auth status redirects to the login page.
        void queryClient.invalidateQueries();
        return;
      }
      retryTimer = setTimeout(connect, retryDelay(attempt));
      attempt += 1;
    }

    function connect() {
      socket = new WebSocket(eventsUrl());
      socket.addEventListener("open", () => {
        attempt = 0;
        // Catch up on anything missed while disconnected.
        void queryClient.invalidateQueries({ queryKey: JOBS_KEY });
      });
      socket.addEventListener("message", (message: MessageEvent<string>) => {
        applyJobEvent(queryClient, JSON.parse(message.data) as JobEvent);
      });
      socket.addEventListener("close", handleClose);
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, [queryClient]);
}
