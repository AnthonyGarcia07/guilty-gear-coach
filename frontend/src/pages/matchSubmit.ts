import type { NavigateFunction } from "react-router-dom";
import type { Match, MatchInput } from "../types";

type MatchApi = {
  createMatch: (payload: MatchInput) => Promise<Match>;
  updateMatch: (id: number, payload: Partial<MatchInput>) => Promise<Match>;
};

const createdMessage = "Match created successfully.";
const updatedMessage = "Match updated successfully.";

export async function submitNewMatch(payload: MatchInput, api: MatchApi, navigate: NavigateFunction) {
  await api.createMatch(payload);
  navigate("/matches", { state: { message: createdMessage } });
}

export async function submitMatchUpdate(matchId: number, payload: MatchInput, api: MatchApi, navigate: NavigateFunction) {
  await api.updateMatch(matchId, payload);
  navigate("/matches", { state: { message: updatedMessage } });
}
