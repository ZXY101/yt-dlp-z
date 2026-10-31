import { Send } from "lucide-react";

import { describeError } from "@/api/errors";
import { CheckboxField } from "@/components/checkbox-field";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { SuccessMessage } from "@/components/success-message";
import { Button } from "@/components/ui/button";
import {
  type NotificationForm,
  useNotificationForm,
} from "@/features/settings/hooks/use-notification-form";
import {
  useNotificationSettings,
  useSaveNotifications,
  useTestNotification,
} from "@/features/settings/notifications-api";
import type { NotificationSettings, NotifyEvent } from "@/features/settings/types";

const EVENTS: { value: NotifyEvent; label: string; description: string }[] = [
  { value: "recording_started", label: "Recording started", description: "A live stream began." },
  { value: "download_finished", label: "Finished", description: "Downloads and recordings." },
  { value: "download_failed", label: "Failed", description: "With the error yt-dlp gave." },
  {
    value: "problems",
    label: "Problems",
    description: "Cookies that YouTube no longer accepts, or several failures in a row.",
  },
];

function TokenField({ form, hasToken }: { form: NotificationForm; hasToken: boolean }) {
  const { token, setToken } = form.fields;
  const removing = hasToken && form.removeToken;
  return (
    <>
      <FormField
        label="Access token"
        type="password"
        autoComplete="off"
        hint={hasToken ? "A token is saved. Type a new one to replace it." : "Optional."}
        placeholder={hasToken ? "••••••••" : undefined}
        value={token}
        disabled={removing}
        onChange={(event) => setToken(event.target.value)}
      />
      {hasToken && (
        <CheckboxField
          label="Remove the saved token"
          checked={form.removeToken}
          onCheckedChange={form.setRemoveToken}
        />
      )}
    </>
  );
}

function EventFields({ form }: { form: NotificationForm }) {
  const { events, toggleEvent } = form.fields;
  return (
    <fieldset className="space-y-1">
      <legend className="mb-1 text-sm font-medium">Notify me when</legend>
      {EVENTS.map((event) => (
        <CheckboxField
          key={event.value}
          label={event.label}
          description={event.description}
          checked={events.includes(event.value)}
          onCheckedChange={(on) => toggleEvent(event.value, on)}
        />
      ))}
    </fieldset>
  );
}

function ServerFields({ form }: { form: NotificationForm }) {
  const { server, setServer, topic, setTopic } = form.fields;
  return (
    <>
      <FormField
        label="Server"
        inputMode="url"
        spellCheck={false}
        value={server}
        onChange={(event) => setServer(event.target.value)}
      />
      <FormField
        label="Topic"
        hint="Subscribe to it in the ntfy app. Anyone who knows a topic on ntfy.sh can read it, so pick one that's hard to guess. Empty turns notifications off."
        spellCheck={false}
        autoCapitalize="off"
        value={topic}
        error={form.topicError}
        onChange={(event) => setTopic(event.target.value)}
      />
    </>
  );
}

function NotificationsForm({ saved }: { saved: NotificationSettings }) {
  const form = useNotificationForm(saved);
  const save = useSaveNotifications();
  const test = useTestNotification();
  const failed = [save, test].find((mutation) => mutation.isError);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const body = form.request();
    if (body) {
      test.reset();
      save.mutate(body, { onSuccess: form.clearToken });
    }
  }

  function sendTest() {
    const body = form.request();
    if (body) {
      save.reset();
      test.mutate(body);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit} noValidate>
      <FormError message={failed ? describeError(failed.error) : null} />
      {save.isSuccess && <SuccessMessage>Notification settings saved.</SuccessMessage>}
      {test.isSuccess && <SuccessMessage>Test message sent. Check your phone.</SuccessMessage>}
      <ServerFields form={form} />
      <TokenField form={form} hasToken={saved.has_token} />
      <EventFields form={form} />
      <div className="flex flex-wrap gap-2">
        <Button type="submit" className="h-10" disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save notifications"}
        </Button>
        <Button
          type="button"
          variant="outline"
          className="h-10"
          disabled={test.isPending}
          onClick={sendTest}
        >
          <Send aria-hidden />
          {test.isPending ? "Sending…" : "Send test message"}
        </Button>
      </div>
    </form>
  );
}

/** Push notifications through ntfy (ntfy.sh or a self-hosted server). */
export function NotificationsSection() {
  const settings = useNotificationSettings();
  return (
    <section className="space-y-4 border-t pt-6" aria-labelledby="notifications-heading">
      <div className="space-y-1">
        <h2 id="notifications-heading" className="text-lg font-medium">
          Notifications
        </h2>
        <p className="text-sm text-muted-foreground">
          Sent to your phone or desktop through{" "}
          <a
            href="https://ntfy.sh"
            target="_blank"
            rel="noreferrer"
            className="underline underline-offset-2"
          >
            ntfy
          </a>
          .
        </p>
      </div>
      {settings.isError && <FormError message={describeError(settings.error)} />}
      {settings.data && <NotificationsForm saved={settings.data} />}
    </section>
  );
}
