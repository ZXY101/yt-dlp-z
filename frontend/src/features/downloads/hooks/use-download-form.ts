import { useState } from "react";
import { useNavigate } from "react-router";

import { useCreateJob } from "@/features/downloads/api";
import {
  type CommonChoices,
  DEFAULT_CHOICES,
  buildOptions,
  validateUrl,
} from "@/features/downloads/options";

export function useDownloadForm() {
  const [url, setUrl] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [extraArgs, setExtraArgs] = useState("");
  const [choices, setChoices] = useState<CommonChoices>(DEFAULT_CHOICES);
  const [urlError, setUrlError] = useState<string>();
  const createJob = useCreateJob();
  const navigate = useNavigate();

  function updateChoices(changes: Partial<CommonChoices>) {
    setChoices((current) => ({ ...current, ...changes }));
  }

  function submit() {
    const error = validateUrl(url);
    setUrlError(error);
    if (error) {
      return;
    }
    const body = {
      url: url.trim(),
      options: buildOptions(choices),
      extra_args: extraArgs,
      output_dir: outputDir.trim() || null,
    };
    createJob.mutate(body, { onSuccess: () => void navigate("/queue") });
  }

  return {
    fields: { url, outputDir, extraArgs },
    setters: { setUrl, setOutputDir, setExtraArgs },
    choices,
    updateChoices,
    urlError,
    submit,
    createJob,
  };
}

export type DownloadForm = ReturnType<typeof useDownloadForm>;
