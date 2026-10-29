import { useState } from "react";

import { useSetup } from "@/features/auth/api";
import type { AuthStatus } from "@/features/auth/types";
import { type PasswordMode, type SetupErrors, validateSetup } from "@/features/auth/validation";

function passwordModeFor(status: AuthStatus): PasswordMode {
  if (status.auth_mode === "none") {
    return "none";
  }
  return status.password_from_env ? "verify" : "create";
}

export function useSetupForm(status: AuthStatus) {
  const passwordMode = passwordModeFor(status);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [downloadDir, setDownloadDir] = useState(status.default_download_dir);
  const [errors, setErrors] = useState<SetupErrors>({});
  const setup = useSetup();

  function submit() {
    const nextErrors = validateSetup({ password, confirmPassword, downloadDir, passwordMode });
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }
    setup.mutate({
      password: passwordMode === "none" ? null : password,
      download_dir: downloadDir.trim(),
    });
  }

  return {
    passwordMode,
    fields: { password, confirmPassword, downloadDir },
    setters: { setPassword, setConfirmPassword, setDownloadDir },
    errors,
    submit,
    setup,
  };
}
