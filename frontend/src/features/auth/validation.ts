export const MIN_PASSWORD_LENGTH = 8;

interface SetupValues {
  password: string;
  confirmPassword: string;
  downloadDir: string;
  needsPassword: boolean;
}

export type SetupErrors = Partial<Record<"password" | "confirmPassword" | "downloadDir", string>>;

function isAbsolutePath(path: string) {
  return path.startsWith("/") || /^[A-Za-z]:[\\/]/.test(path);
}

function passwordErrors({ password, confirmPassword }: SetupValues): SetupErrors {
  if (password.length < MIN_PASSWORD_LENGTH) {
    return { password: `Use at least ${MIN_PASSWORD_LENGTH} characters.` };
  }
  if (password !== confirmPassword) {
    return { confirmPassword: "Passwords don't match." };
  }
  return {};
}

export function validateSetup(values: SetupValues): SetupErrors {
  const errors = values.needsPassword ? passwordErrors(values) : {};
  const downloadDir = values.downloadDir.trim();
  if (!downloadDir) {
    errors.downloadDir = "Choose a download folder.";
  } else if (!isAbsolutePath(downloadDir)) {
    errors.downloadDir = "Use a full path, e.g. /downloads.";
  }
  return errors;
}
