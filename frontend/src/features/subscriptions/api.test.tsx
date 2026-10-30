import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";

import { createQueryClient } from "@/app/query-client";
import { useSubscriptionVideos } from "@/features/subscriptions/api";
import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeVideo } from "@/test/fake-subscriptions";

describe("useSubscriptionVideos", () => {
  it("reloads the videos as soon as a check ends", async () => {
    // Regression: polling stopped when the check ended, so videos written at the very
    // end of a check could stay missing until the page was reloaded.
    const server = createFakeServer();
    server.videos = { 5: [] };
    installFakeApi(server);
    const client = createQueryClient();
    const { result, rerender } = renderHook(({ checking }) => useSubscriptionVideos(5, checking), {
      initialProps: { checking: true },
      wrapper: ({ children }) => (
        <QueryClientProvider client={client}>{children}</QueryClientProvider>
      ),
    });
    await waitFor(() => expect(result.current.data).toEqual([]));

    server.videos = { 5: [makeVideo({ title: "Found at the end" })] };
    rerender({ checking: false });
    await waitFor(() => expect(result.current.data).toHaveLength(1), { timeout: 1000 });
  });
});
