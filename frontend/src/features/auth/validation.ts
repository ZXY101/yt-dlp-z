export const MIN_PASSWORD_LENGTH = 8;

/** create: choose a new password. verify: enter the one set by YTDLPZ_ADMIN_PASSWORD.
 * none: a reverse proxy handles login. */
export type PasswordMode = "create" | "verify" | "none";

interface SetupValues {
  password: string;
  confirmPassword: string;
  downloadDir: string;
  passwordMode: PasswordMode;
}

export type SetupErrors = Partial<Record<"password" | "confirmPassword" | "downloadDir", string>>;

function isAbsolutePath(path: string) {
  return path.startsWith("/") || /^[A-Za-z]:[\\/]/.test(path);
}

function passwordErrors({ password, confirmPassword, passwordMode }: SetupValues): SetupErrors {
  if (passwordMode === "none") {
    return {};
  }
  if (passwordMode === "verify") {
    return password ? {} : { password: "Enter the admin password." };
  }
  if (password.length < MIN_PASSWORD_LENGTH) {
    return { password: `Use at least ${MIN_PASSWORD_LENGTH} characters.` };
  }
  if (password !== confirmPassword) {
    return { confirmPassword: "Passwords don't match." };
  }
  return {};
}

export function validateSetup(values: SetupValues): SetupErrors {
  const errors = passwordErrors(values);
  const downloadDir = values.downloadDir.trim();
  if (!downloadDir) {
    errors.downloadDir = "Choose a download folder.";
  } else if (!isAbsolutePath(downloadDir)) {
    errors.downloadDir = "Use a full path, e.g. /downloads.";
  }
  return errors;
}
