import { describe, expect, it } from "vitest";
import { guessPage } from "./page-guess.ts";

const server = { serverAddress: "http://zxy-server:9742" };

describe("guessPage", () => {
  it("knows the user's own server, by address or by the dashboard's tab title", () => {
    expect(guessPage("http://zxy-server:9742/queue", server)).toBe("own-server");
    const elsewhere = { serverAddress: null, title: "yt-dlp-z" };
    expect(guessPage("https://yt.example.org/", elsewhere)).toBe("own-server");
  });

  it("leaves other apps on the same machine to the server", () => {
    expect(guessPage("http://zxy-server:8096/web", server)).toBe("unknown");
  });

  it("knows addresses that mean the server itself", () => {
    expect(guessPage("http://localhost:8080/video.mp4", server)).toBe("this-computer");
    expect(guessPage("http://127.0.0.1/clip", server)).toBe("this-computer");
  });

  it("otherwise guesses from the link", () => {
    expect(guessPage("https://youtu.be/abc", server)).toBe("video");
    expect(guessPage("chrome://extensions", server)).toBe("unsupported");
  });
});
