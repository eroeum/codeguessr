import { Routes } from '@angular/router';
import { GameComponent } from './game/game.component';
import { ResultsComponent } from './results/results.component';
import { SettingsComponent } from './settings/settings.component';

export const routes: Routes = [
  { path: '',        component: SettingsComponent },
  { path: 'game',    component: GameComponent },
  { path: 'results', component: ResultsComponent },
  { path: '**',      redirectTo: '' },
];
