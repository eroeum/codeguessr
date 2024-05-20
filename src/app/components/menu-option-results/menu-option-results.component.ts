import { Component, forwardRef } from '@angular/core';
import { MenuOption } from '../menu-bar/menu-bar';
import {MatButtonModule} from '@angular/material/button';
import { Store } from '@ngrx/store';
import { AppState } from '../../state';
import { selectGuessResults, selectSelectedFile } from '../../state/game.selector';
import { CommonModule } from '@angular/common';
import { map } from 'rxjs';
import { startGame } from '../../state/game.actions';
import { CodeService } from '../../services/code.service';

class MenuOptionResult extends MenuOption {
  tabIcon = 'sports_score';
  name ='Results';
}

@Component({
  selector: 'app-menu-option-results',
  standalone: true,
  imports: [CommonModule, MatButtonModule],
  templateUrl: './menu-option-results.component.html',
  styleUrl: './menu-option-results.component.scss',
  providers: [{ provide: MenuOption, useValue: forwardRef(() => new MenuOptionResult()) }]
})
export class MenuOptionResultsComponent {
  
  constructor(
    private store: Store<AppState>,
    private codeService: CodeService,
  ) {}

  fileFilterForm = this.codeService.fileFilterForm;
  isGuessCorrect$ = this.store.select(selectGuessResults);
  selectedFile$ = this.store.select(selectSelectedFile).pipe(
    map((selected) => {
      const path = (selected?.path || '') as string;
      const fullPath = path.length ? `${path}/${selected?.file_name}` : selected?.file_name;
      return fullPath;
    })
  );

  newRound() {
    this.store.dispatch(startGame({ payload: {
      include: this.fileFilterForm.get('include')?.value || '',
      exclude: this.fileFilterForm.get('exclude')?.value || '',
    }}))

  }
}
