import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import type { PresetIn } from "@/features/presets/types";

const PRESETS_KEY = ["presets"];

function presetPath(presetId: number) {
  return { params: { path: { preset_id: presetId } } };
}

export function usePresets() {
  return useQuery({ queryKey: PRESETS_KEY, queryFn: () => unwrap(api.GET("/api/presets")) });
}

function usePresetMutation<T>(send: (input: T) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: send,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PRESETS_KEY }),
  });
}

/** Creates a preset, or updates it when an id is given. */
export function useSavePreset() {
  return usePresetMutation(({ id, body }: { id: number | null; body: PresetIn }) => {
    if (id === null) {
      return unwrap(api.POST("/api/presets", { body }));
    }
    return unwrap(api.PUT("/api/presets/{preset_id}", { ...presetPath(id), body }));
  });
}

export function useDeletePreset() {
  return usePresetMutation((id: number) =>
    unwrap(api.DELETE("/api/presets/{preset_id}", presetPath(id))),
  );
}
