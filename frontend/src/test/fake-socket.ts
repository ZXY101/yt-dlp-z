type Listener = (event: { data?: string; code?: number }) => void;

const CONNECTING = 0;
const OPEN = 1;
const CLOSED = 3;

/** Minimal WebSocket stand-in: opens on the next tick and lets tests push events. */
export class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  readonly url: string;
  readyState = CONNECTING;
  private listeners = new Map<string, Listener[]>();

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
    queueMicrotask(() => {
      if (this.readyState === CONNECTING) {
        this.readyState = OPEN;
        this.dispatch("open", {});
      }
    });
  }

  addEventListener(type: string, listener: Listener) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }

  close(code = 1000) {
    if (this.readyState === CLOSED) {
      return;
    }
    this.readyState = CLOSED;
    this.dispatch("close", { code });
  }

  dispatch(type: string, event: { data?: string; code?: number }) {
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event);
    }
  }
}

export function broadcast(event: unknown) {
  for (const socket of FakeWebSocket.instances) {
    if (socket.readyState === OPEN) {
      socket.dispatch("message", { data: JSON.stringify(event) });
    }
  }
}

export function installFakeSocket() {
  FakeWebSocket.instances = [];
  vi.stubGlobal("WebSocket", FakeWebSocket);
}
