import { CheckboxField } from "@/components/checkbox-field";
import { FormField } from "@/components/form-field";
import type { FormErrors, SubscriptionFormValues } from "@/features/subscriptions/form-values";
import type { ContentType } from "@/features/subscriptions/types";

const CONTENT_TYPES: { value: ContentType; label: string; description: string }[] = [
  { value: "video", label: "Videos", description: "Regular uploads." },
  { value: "short", label: "Shorts", description: "Vertical videos up to 3 minutes." },
  {
    value: "stream",
    label: "Live streams and premieres",
    description: "Listed for now; recording them comes in a later version.",
  },
];

interface FilterFieldsProps {
  values: SubscriptionFormValues;
  errors: FormErrors;
  onChange: (changes: Partial<SubscriptionFormValues>) => void;
}

function ContentTypeFields({ values, errors, onChange }: FilterFieldsProps) {
  function toggle(type: ContentType, checked: boolean) {
    const others = values.contentTypes.filter((item) => item !== type);
    onChange({ contentTypes: checked ? [...others, type] : others });
  }

  return (
    <fieldset className="space-y-1" aria-describedby="content-types-error">
      <legend className="mb-1 text-sm font-medium">Download</legend>
      {CONTENT_TYPES.map((type) => (
        <CheckboxField
          key={type.value}
          label={type.label}
          description={type.description}
          checked={values.contentTypes.includes(type.value)}
          onCheckedChange={(checked) => toggle(type.value, checked)}
        />
      ))}
      {errors.contentTypes && (
        <p id="content-types-error" className="text-sm text-destructive">
          {errors.contentTypes}
        </p>
      )}
    </fieldset>
  );
}

function TitleAndDurationFields({ values, errors, onChange }: FilterFieldsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <FormField
        label="Title must match"
        placeholder="e.g. podcast|episode"
        hint="A regular expression, case-insensitive."
        spellCheck={false}
        value={values.titleInclude}
        onChange={(event) => onChange({ titleInclude: event.target.value })}
      />
      <FormField
        label="Skip titles matching"
        placeholder="e.g. trailer|teaser"
        spellCheck={false}
        value={values.titleExclude}
        onChange={(event) => onChange({ titleExclude: event.target.value })}
      />
      <FormField
        label="Shortest (minutes)"
        inputMode="decimal"
        value={values.minMinutes}
        error={errors.minMinutes}
        onChange={(event) => onChange({ minMinutes: event.target.value })}
      />
      <FormField
        label="Longest (minutes)"
        inputMode="decimal"
        value={values.maxMinutes}
        error={errors.maxMinutes}
        onChange={(event) => onChange({ maxMinutes: event.target.value })}
      />
    </div>
  );
}

export function FilterFields(props: FilterFieldsProps) {
  const { values, onChange } = props;
  return (
    <section className="space-y-4" aria-labelledby="filters-heading">
      <h2 id="filters-heading" className="text-base font-semibold">
        Which uploads to download
      </h2>
      <ContentTypeFields {...props} />
      <TitleAndDurationFields {...props} />
      <FormField
        label="Only uploads published on or after"
        type="date"
        value={values.publishedAfter}
        onChange={(event) => onChange({ publishedAfter: event.target.value })}
      />
      <CheckboxField
        label="Include members-only videos"
        description="Needs cookies from a channel member, set here or in the preset."
        checked={values.includeMembersOnly}
        onCheckedChange={(includeMembersOnly) => onChange({ includeMembersOnly })}
      />
    </section>
  );
}
