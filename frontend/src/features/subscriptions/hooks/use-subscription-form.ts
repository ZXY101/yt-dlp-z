import { useState } from "react";
import { useNavigate } from "react-router";

import { useCreateSubscription, useUpdateSubscription } from "@/features/subscriptions/api";
import {
  EMPTY_FORM,
  type FormErrors,
  type SubscriptionFormValues,
  createBody,
  formFromSubscription,
  updateBody,
  validateForm,
} from "@/features/subscriptions/form-values";
import type { Subscription } from "@/features/subscriptions/types";

export function useSubscriptionForm(subscription: Subscription | null) {
  const [values, setValues] = useState(() =>
    subscription ? formFromSubscription(subscription) : EMPTY_FORM,
  );
  const [errors, setErrors] = useState<FormErrors>({});
  const create = useCreateSubscription();
  const update = useUpdateSubscription();
  const navigate = useNavigate();
  const save = subscription ? update : create;

  function change(changes: Partial<SubscriptionFormValues>) {
    setValues((current) => ({ ...current, ...changes }));
  }

  function submit() {
    const found = validateForm(values, subscription === null);
    setErrors(found);
    if (Object.keys(found).length > 0) {
      return;
    }
    const done = { onSuccess: () => void navigate("/subscriptions") };
    if (subscription) {
      update.mutate({ id: subscription.id, body: updateBody(values) }, done);
    } else {
      create.mutate(createBody(values), done);
    }
  }

  return { values, errors, change, submit, save };
}
