import { useState } from "react";

import { useSetup } from "@/features/auth/api";
import type { AuthStatus } from "@/features/auth/types";
import { type SetupErrors, validateSetup } from "@/features/auth/validation";

export function useSetupForm(status: AuthStatus) {
  const needsPassword = status.auth_mode === "password";
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [downloadDir, setDownloadDir] = useState(status.default_download_dir);
  const [errors, setErrors] = useState<SetupErrors>({});
  const setup = useSetup();

  function submit() {
    const nextErrors = validateSetup({ password, confirmPassword, downloadDir, needsPassword });
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }
    setup.mutate({
      password: needsPassword ? password : null,
      download_dir: downloadDir.trim(),
    });
  }

  return {
    needsPassword,
    fields: { password, confirmPassword, downloadDir },
    setters: { setPassword, setConfirmPassword, setDownloadDir },
    errors,
    submit,
    setup,
  };
}
