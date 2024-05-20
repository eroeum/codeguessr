import { createSelector } from '@ngrx/store';
import * as fromGame from './game.reducer';
import { AppState } from '.';

export const selectFeature = (state: AppState) => state.GameState;

export const selectState = createSelector(
    selectFeature,
    (state: fromGame.AppState) => state.state,
)

export const selectFiles = createSelector(
    selectFeature,
    (state: fromGame.AppState) => state.files,
)

export const selectSelectedFile = createSelector(
    selectFeature,
    (state: fromGame.AppState) => state.selectedFile,
)

export const selectFileSelectionIsLoading = createSelector(
    selectFeature,
    (state: fromGame.AppState) => state.fileIsLoading,
)

export const selectGuessResults = createSelector(
    selectFeature,
    (state: fromGame.AppState) => state.isGuessCorrect,
)
