import { useState } from "react";

import { describeError } from "@/api/errors";
import { FieldShell } from "@/components/field-shell";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUploadCookieFile } from "@/features/cookies/api";

interface UploadErrors {
  name?: string;
  file?: string;
}

function validate(name: string, file: File | null): UploadErrors {
  return {
    name: name.trim() ? undefined : "Give the file a name, e.g. YouTube.",
    file: file ? undefined : "Choose a cookies.txt file.",
  };
}

function useUploadForm() {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<UploadErrors>({});
  // Changing the key clears the file input after an upload.
  const [inputKey, setInputKey] = useState(0);
  const upload = useUploadCookieFile();

  function reset() {
    setName("");
    setFile(null);
    setInputKey(inputKey + 1);
  }

  async function submit() {
    const found = validate(name, file);
    setErrors(found);
    if (found.name || found.file || !file) {
      return;
    }
    const content = await file.text();
    upload.mutate({ name: name.trim(), content }, { onSuccess: reset });
  }

  return { name, setName, setFile, errors, inputKey, upload, submit };
}

export function CookieUploadForm() {
  const { name, setName, setFile, errors, inputKey, upload, submit } = useUploadForm();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submit();
  }

  return (
    <form className="space-y-4 rounded-xl border p-4" onSubmit={handleSubmit} noValidate>
      <h2 className="text-lg font-medium">Add cookies</h2>
      <FormError message={upload.isError ? describeError(upload.error) : null} />
      <FormField
        label="Name"
        placeholder="YouTube"
        value={name}
        error={errors.name}
        onChange={(event) => setName(event.target.value)}
      />
      <FieldShell
        label="Cookies file"
        hint="A Netscape-format cookies.txt, exported with a browser extension."
        error={errors.file}
      >
        {(control) => (
          <Input
            key={inputKey}
            {...control}
            type="file"
            accept=".txt,text/plain"
            className="h-10"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        )}
      </FieldShell>
      <Button type="submit" className="h-10" disabled={upload.isPending}>
        {upload.isPending ? "Uploading…" : "Upload"}
      </Button>
    </form>
  );
}
