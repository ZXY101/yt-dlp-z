import { FormField } from "@/components/form-field";
import type { useSetupForm } from "@/features/auth/hooks/use-setup-form";
import { MIN_PASSWORD_LENGTH } from "@/features/auth/validation";

interface PasswordFieldsProps {
  form: ReturnType<typeof useSetupForm>;
}

export function PasswordFields({ form }: PasswordFieldsProps) {
  return (
    <>
      <FormField
        label="Admin password"
        type="password"
        autoComplete="new-password"
        hint={`At least ${MIN_PASSWORD_LENGTH} characters.`}
        required
        value={form.fields.password}
        error={form.errors.password}
        onChange={(event) => form.setters.setPassword(event.target.value)}
      />
      <FormField
        label="Repeat password"
        type="password"
        autoComplete="new-password"
        required
        value={form.fields.confirmPassword}
        error={form.errors.confirmPassword}
        onChange={(event) => form.setters.setConfirmPassword(event.target.value)}
      />
    </>
  );
}
