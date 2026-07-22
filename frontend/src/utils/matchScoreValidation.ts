import type { Result } from "../types";

export const maxSetScore = 10;

export interface ScoreValidationInput {
  result: Result;
  roundsWon: string;
  roundsLost: string;
  firstTo: string;
}

export interface ScoreValidationErrors {
  rounds_won?: string;
  rounds_lost?: string;
  first_to?: string;
}

export function validateMatchScore(input: ScoreValidationInput): ScoreValidationErrors {
  const errors: ScoreValidationErrors = {};
  const roundsWon = parseOptionalInteger(input.roundsWon);
  const roundsLost = parseOptionalInteger(input.roundsLost);
  const firstTo = parseOptionalInteger(input.firstTo);
  const scoreValues = [roundsWon, roundsLost, firstTo];

  if (scoreValues.every((value) => value === null)) return errors;
  if (scoreValues.some((value) => value === null)) {
    errors.rounds_won = "Enter your score, opponent score, and first-to format together.";
    return errors;
  }
  const completedRoundsWon = roundsWon as number;
  const completedRoundsLost = roundsLost as number;
  const completedFirstTo = firstTo as number;

  if (!Number.isFinite(completedRoundsWon) || completedRoundsWon < 0) errors.rounds_won = "Your set score must be 0 or greater.";
  if (!Number.isFinite(completedRoundsLost) || completedRoundsLost < 0) errors.rounds_lost = "Opponent set score must be 0 or greater.";
  if (!Number.isFinite(completedFirstTo) || completedFirstTo < 1) errors.first_to = "First-to must be greater than 0.";
  if (errors.rounds_won || errors.rounds_lost || errors.first_to) return errors;
  if (completedRoundsWon > maxSetScore || completedRoundsLost > maxSetScore || completedFirstTo > maxSetScore) {
    errors.rounds_won = `Set scores must be ${maxSetScore} or lower.`;
    return errors;
  }
  if (completedRoundsWon === completedRoundsLost) {
    errors.rounds_won = "Completed set score cannot be tied.";
    return errors;
  }
  if (Math.max(completedRoundsWon, completedRoundsLost) !== completedFirstTo || Math.min(completedRoundsWon, completedRoundsLost) >= completedFirstTo) {
    errors.rounds_won = "Completed set score must have exactly one side reaching the selected first-to value.";
    return errors;
  }
  if (input.result === "win" && completedRoundsWon <= completedRoundsLost) errors.rounds_won = "A win must have your score ahead of the opponent.";
  if (input.result === "loss" && completedRoundsLost <= completedRoundsWon) errors.rounds_lost = "A loss must have the opponent score ahead of yours.";
  return errors;
}

function parseOptionalInteger(value: string) {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : Number.NaN;
}
