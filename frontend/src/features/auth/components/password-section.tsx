import { type FormEvent, useState } from "react";

import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { SuccessMessage } from "@/components/success-message";
import { Button } from "@/components/ui/button";
import { useAuthStatus, useChangePassword } from "@/features/auth/api";
import { MIN_PASSWORD_LENGTH } from "@/features/auth/validation";

type PasswordErrors = Partial<Record<"newPassword" | "repeat", string>>;

function checkNewPassword(newPassword: string, repeat: string): PasswordErrors {
  if (newPassword.length < MIN_PASSWORD_LENGTH) {
    return { newPassword: `Use at least ${MIN_PASSWORD_LENGTH} characters.` };
  }
  return newPassword === repeat ? {} : { repeat: "Passwords don't match." };
}

type Field = "current" | "newPassword" | "repeat";

const FIELDS: { name: Field; label: string; autoComplete: string }[] = [
  { name: "current", label: "Current password", autoComplete: "current-password" },
  { name: "newPassword", label: "New password", autoComplete: "new-password" },
  { name: "repeat", label: "Repeat new password", autoComplete: "new-password" },
];

const EMPTY: Record<Field, string> = { current: "", newPassword: "", repeat: "" };

function ChangePasswordForm() {
  const change = useChangePassword();
  const [values, setValues] = useState(EMPTY);
  const [errors, setErrors] = useState<PasswordErrors>({});

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const found = checkNewPassword(values.newPassword, values.repeat);
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    const body = { current_password: values.current, new_password: values.newPassword };
    change.mutate(body, { onSuccess: () => setValues(EMPTY) });
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit} noValidate>
      {FIELDS.map((field) => (
        <FormField
          key={field.name}
          label={field.label}
          type="password"
          autoComplete={field.autoComplete}
          error={field.name === "current" ? undefined : errors[field.name]}
          value={values[field.name]}
          onChange={(event) => setValues({ ...values, [field.name]: event.target.value })}
        />
      ))}
      <FormError message={change.isError ? describeError(change.error) : null} />
      {change.isSuccess && (
        <SuccessMessage>
          Password changed. Other browsers and devices were signed out.
        </SuccessMessage>
      )}
      <Button type="submit" className="h-10" disabled={!values.current || change.isPending}>
        {change.isPending ? "Changing…" : "Change password"}
      </Button>
    </form>
  );
}

/** Settings → Password. Hidden without a password; points to the env variable when it's set. */
export function PasswordSection() {
  const status = useAuthStatus();
  if (!status.data || status.data.auth_mode === "none") return null;
  return (
    <section className="space-y-4 border-t pt-6" aria-labelledby="password-heading">
      <div className="space-y-1">
        <h2 id="password-heading" className="text-lg font-medium">
          Password
        </h2>
        <p className="text-sm text-muted-foreground">
          Changing it signs out every other browser and device. API tokens keep working.
        </p>
      </div>
      {status.data.password_from_env ? (
        <p className="text-sm text-muted-foreground">
          The password is set by <code>YTDLPZ_ADMIN_PASSWORD</code>. Change it there and restart
          yt-dlp-z.
        </p>
      ) : (
        <ChangePasswordForm />
      )}
    </section>
  );
}
