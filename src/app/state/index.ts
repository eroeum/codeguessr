import * as fromGame from './game.reducer';

export interface AppState {
    [fromGame.FEATURE_KEY]: fromGame.AppState,
}
