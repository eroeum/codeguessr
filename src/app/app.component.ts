import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Store } from '@ngrx/store';
import { EditorComponent } from './components/editor/editor.component';
import { MenuBarComponent } from './components/menu-bar/menu-bar.component';
import { AppState } from './state';
import { fileDataRequest } from './state/game.actions';
import { selectState } from './state/game.selector';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, MenuBarComponent, EditorComponent, MatProgressSpinnerModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'codeguessr';

  gameState$ = this.store.select(selectState);

  constructor(
    private store: Store<AppState>,
  ) {}

  ngOnInit(): void {
    this.store.dispatch(fileDataRequest());
  }
}
