import type { QuestionnaireAvatarPreview } from "../../services/partnerAQuestionnaireService";
import type { AvatarConfig } from "../avatar/avataaarsVariants";

export function applyQuestionnaireAvatarPreviews(
  base: AvatarConfig,
  previews: QuestionnaireAvatarPreview[],
  selections: Record<string, string>,
  player: "partner_a" | "partner_b",
): AvatarConfig {
  const next: AvatarConfig = { ...base };
  for (const preview of previews) {
    if (preview.player !== player) {
      continue;
    }
    if (selections[preview.question_id] !== preview.option_id) {
      continue;
    }
    if (preview.attribute === "accessoriesProbability") {
      next.accessoriesProbability = Number(preview.value);
      continue;
    }
    if (preview.attribute === "facialHairProbability") {
      next.facialHairProbability = Number(preview.value);
      continue;
    }
    (next as Record<string, string | number>)[preview.attribute] =
      preview.value;
  }
  return next;
}
