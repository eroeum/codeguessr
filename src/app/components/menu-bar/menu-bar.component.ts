import { AfterViewInit, ChangeDetectorRef, Component, Input, OnInit, QueryList, ViewChildren } from '@angular/core';
import {MatTabsModule} from '@angular/material/tabs';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';
import { MenuOption } from './menu-bar';
import { MenuOptionExplorerComponent } from '../menu-option-explorer/menu-option-explorer.component';
import { CommonModule } from '@angular/common';
import { MenuOptionGameComponent } from '../menu-option-game/menu-option-game.component';
import { Store } from '@ngrx/store';
import { AppState } from '../../state';
import { Observable } from 'rxjs';
import { selectState } from '../../state/game.selector';
import { MenuOptionResultsComponent } from '../menu-option-results/menu-option-results.component';

@Component({
  selector: 'app-menu-bar',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    MatIconModule,
    MatTooltipModule,
    MenuOptionExplorerComponent,
    MenuOptionGameComponent,
    MenuOptionResultsComponent,
  ],
  templateUrl: './menu-bar.component.html',
  styleUrl: './menu-bar.component.scss'
})
export class MenuBarComponent implements OnInit, AfterViewInit {

  menuOptions?: MenuOption[];

  state$ = this.store.select(selectState)

  @Input()
  selectedOptionIndex: number = 0;

  constructor(private cdr: ChangeDetectorRef, private store: Store<AppState>) {}

  @ViewChildren(MenuOption) options!: QueryList<MenuOption>;

  ngOnInit(): void {
      this.state$.subscribe((state) => {
        if (state === 'Game Configuration') {
          this.selectedOptionIndex = 0;
        }

        if (state === 'Game') {
          this.selectedOptionIndex = 1;
        }

        if (state === 'Game Finish') {
          this.selectedOptionIndex = 2;
        }
      })
  }

  ngAfterViewInit(): void {
    this.menuOptions = this.options.toArray();
    this.cdr.detectChanges();
  }
}
