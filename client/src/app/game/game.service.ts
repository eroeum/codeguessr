import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface GameSettings {
  num_rounds: number;
  max_guesses: number;
  min_line_chars: number;
  min_lines: number;
  include_pattern: string;
  ignore_pattern: string;
}

export const DEFAULT_SETTINGS: GameSettings = {
  num_rounds: 5,
  max_guesses: 6,
  min_line_chars: 1,
  min_lines: 10,
  include_pattern: '',
  ignore_pattern: '',
};

export interface NewGameResponse {
  game_id: string;
  files: string[];
  total_rounds: number;
  max_guesses: number;
  round_num: number;
  code_display: string;
  highlight_line: number;
  potential_score: number;
  guesses_remaining: number;
  wrong_guesses: string[];
  language: string;
}

export interface CompletedRound {
  round_num: number;
  target_file: string;
  round_points: number;
  wrong_guesses: string[];
  correct: boolean;
}

export interface RoundSummary {
  round_num: number;
  target_file: string;
  correct: boolean;
  points: number;
  wrong_guesses: string[];
}

export interface GuessResponse {
  correct: boolean;
  round_over: boolean;
  game_over: boolean;
  total_score: number;
  completed_round?: CompletedRound;
  rounds?: RoundSummary[];
  // Next-round payload (present when a round ends but the game continues).
  round_num?: number;
  code_display?: string;
  highlight_line?: number;
  potential_score?: number;
  guesses_remaining?: number;
  wrong_guesses?: string[];
  language?: string;
}

@Injectable({ providedIn: 'root' })
export class GameService {
  private readonly http = inject(HttpClient);
  private readonly apiBase = '/api';

  newGame(settings: GameSettings = DEFAULT_SETTINGS): Observable<NewGameResponse> {
    return this.http.post<NewGameResponse>(`${this.apiBase}/game/new`, settings);
  }

  submitGuess(gameId: string, filePath: string): Observable<GuessResponse> {
    return this.http.post<GuessResponse>(
      `${this.apiBase}/game/${gameId}/guess`,
      { file_path: filePath },
    );
  }
}
