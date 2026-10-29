import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { useAuthStatus } from "@/features/auth/api";
import { AuthCard } from "@/features/auth/components/auth-card";
import { PasswordFields } from "@/features/auth/components/password-fields";
import { useSetupForm } from "@/features/auth/hooks/use-setup-form";
import type { AuthStatus } from "@/features/auth/types";

export function SetupPage() {
  const { data: status } = useAuthStatus();
  // AuthGate only renders this page once the status has loaded.
  if (!status) {
    return null;
  }
  return <SetupForm status={status} />;
}

function SetupForm({ status }: { status: AuthStatus }) {
  const form = useSetupForm(status);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    form.submit();
  }

  return (
    <AuthCard title="Welcome to yt-dlp-z" description="A couple of things before you start.">
      <form className="space-y-4" onSubmit={handleSubmit} noValidate>
        <FormError message={form.setup.isError ? describeError(form.setup.error) : null} />
        {form.passwordMode !== "none" && <PasswordFields form={form} />}
        <FormField
          label="Download folder"
          hint="Where downloads go by default. You can pick another folder per download."
          required
          value={form.fields.downloadDir}
          error={form.errors.downloadDir}
          onChange={(event) => form.setters.setDownloadDir(event.target.value)}
        />
        <Button type="submit" size="lg" className="h-10 w-full" disabled={form.setup.isPending}>
          {form.setup.isPending ? "Saving…" : "Finish setup"}
        </Button>
      </form>
    </AuthCard>
  );
}
