import { CheckboxField } from "@/components/checkbox-field";
import { FormField } from "@/components/form-field";
import {
  type FormErrors,
  MIN_POLL_MINUTES,
  type SubscriptionFormValues,
} from "@/features/subscriptions/form-values";

interface ScheduleFieldsProps {
  values: SubscriptionFormValues;
  errors: FormErrors;
  onChange: (changes: Partial<SubscriptionFormValues>) => void;
}

/** How often the channel is checked, pausing, and how long downloads are kept. */
export function ScheduleFields({ values, errors, onChange }: ScheduleFieldsProps) {
  return (
    <>
      <FormField
        label="Check every (minutes)"
        inputMode="numeric"
        hint={`At least ${MIN_POLL_MINUTES}. Checking often makes rate limits more likely.`}
        value={values.pollMinutes}
        error={errors.pollMinutes}
        onChange={(event) => onChange({ pollMinutes: event.target.value })}
      />
      <CheckboxField
        label="Watch this channel"
        description="Turn off to pause checking without losing the settings."
        checked={values.enabled}
        onCheckedChange={(enabled) => onChange({ enabled })}
      />
      <FormField
        label="Delete downloads after (days)"
        inputMode="numeric"
        hint="Optional. Deletes the files and won't download them again. Downloads you pin with Keep stay. Empty keeps everything."
        value={values.keepDays}
        error={errors.keepDays}
        onChange={(event) => onChange({ keepDays: event.target.value })}
      />
    </>
  );
}
