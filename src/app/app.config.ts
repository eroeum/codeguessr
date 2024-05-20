import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideHttpClient } from '@angular/common/http';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';
import { provideStore } from '@ngrx/store';
import* as fromGame from './state/game.reducer';
import { provideEffects } from '@ngrx/effects';
import { GameEffects } from './state/game.effects';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideClientHydration(),
    provideAnimationsAsync(),
    provideHttpClient(),
    importProvidersFrom(MonacoEditorModule.forRoot()),
    provideStore({ [fromGame.FEATURE_KEY]: fromGame.gameReducer }),
    provideEffects(GameEffects)
  ],
};
