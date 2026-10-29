import { useState } from "react";

import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { useLogin } from "@/features/auth/api";
import { AuthCard } from "@/features/auth/components/auth-card";

export function LoginPage() {
  const [password, setPassword] = useState("");
  const login = useLogin();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate({ password });
  }

  return (
    <AuthCard title="Sign in" description="Enter the admin password to continue.">
      <form className="space-y-4" onSubmit={handleSubmit} noValidate>
        <FormError message={login.isError ? describeError(login.error) : null} />
        <FormField
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" size="lg" className="h-10 w-full" disabled={login.isPending}>
          {login.isPending ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthCard>
  );
}
