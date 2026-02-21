import { Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { DEFAULT_SETTINGS, GameSettings } from '../game/game.service';

const STORAGE_KEY = 'codeguessr_settings';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [FormsModule],
  template: `
<div class="vscode">

  <!-- Tab Bar -->
  <div class="tab-bar">
    <div class="tab tab-active">
      <svg class="tab-icon" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path d="M9.1 4.4L8.6 2H7.4L6.9 4.4C6.3 4.6 5.7 4.9 5.2 5.3L2.9 4.4L2 5.3L3 7.6C2.7 8.1 2.4 8.7 2.3 9.3L0 9.8V11.2L2.4 11.7C2.5 12.3 2.8 12.9 3.1 13.4L2.1 15.7L3 16.6L5.3 15.5C5.8 15.9 6.4 16.2 7 16.4L7.5 18.5H8.9L9.4 16.4C10 16.2 10.6 15.9 11.1 15.5L13.4 16.6L14.3 15.7L13.3 13.4C13.6 12.9 13.9 12.3 14 11.7L16.4 11.2V9.8L14.1 9.3C14 8.7 13.7 8.1 13.4 7.6L14.4 5.3L13.5 4.4L11.2 5.3C10.7 4.9 10.1 4.6 9.5 4.4L9.1 4.4zM8.2 13C6.5 13 5.2 11.7 5.2 10S6.5 7 8.2 7 11.2 8.3 11.2 10 9.9 13 8.2 13z"/>
      </svg>
      Settings
    </div>
  </div>

  <!-- Breadcrumb -->
  <div class="breadcrumb">
    <span class="bc-item">Preferences</span>
    <span class="bc-sep">›</span>
    <span class="bc-item bc-leaf">Settings</span>
  </div>

  <!-- Workbench -->
  <div class="workbench">

    <!-- Activity Bar -->
    <nav class="activitybar">
      <button class="ab-item ab-active" title="Settings">
        <svg viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M9.1 4.4L8.6 2H7.4L6.9 4.4C6.3 4.6 5.7 4.9 5.2 5.3L2.9 4.4L2 5.3L3 7.6C2.7 8.1 2.4 8.7 2.3 9.3L0 9.8V11.2L2.4 11.7C2.5 12.3 2.8 12.9 3.1 13.4L2.1 15.7L3 16.6L5.3 15.5C5.8 15.9 6.4 16.2 7 16.4L7.5 18.5H8.9L9.4 16.4C10 16.2 10.6 15.9 11.1 15.5L13.4 16.6L14.3 15.7L13.3 13.4C13.6 12.9 13.9 12.3 14 11.7L16.4 11.2V9.8L14.1 9.3C14 8.7 13.7 8.1 13.4 7.6L14.4 5.3L13.5 4.4L11.2 5.3C10.7 4.9 10.1 4.6 9.5 4.4L9.1 4.4zM8.2 13C6.5 13 5.2 11.7 5.2 10S6.5 7 8.2 7 11.2 8.3 11.2 10 9.9 13 8.2 13z"/>
        </svg>
      </button>
    </nav>

    <!-- Sidebar nav -->
    <aside class="sidebar">
      <div class="sb-title">SETTINGS</div>
      <div class="sb-nav">
        <div class="sb-nav-item sb-nav-active"
             role="button" tabindex="0"
             (click)="scrollTo('game')"
             (keydown.enter)="scrollTo('game')"
             (keydown.space)="scrollTo('game')">
          <span class="chevron">›</span> Game
        </div>
        <div class="sb-nav-item"
             role="button" tabindex="0"
             (click)="scrollTo('filter')"
             (keydown.enter)="scrollTo('filter')"
             (keydown.space)="scrollTo('filter')">
          <span class="chevron">›</span> File Filter
        </div>
      </div>
    </aside>

    <!-- Content -->
    <main class="settings-content">

      <!-- GAME section -->
      <div class="settings-section" id="section-game">
        <div class="section-header">GAME</div>

        <div class="setting-row">
          <div class="setting-key">codeguessr.rounds</div>
          <div class="setting-desc">Number of rounds per game.</div>
          <input
            class="setting-input setting-number"
            type="number" min="1" max="20"
            [(ngModel)]="settings.num_rounds"
            (ngModelChange)="save()"
          />
        </div>

        <div class="setting-row">
          <div class="setting-key">codeguessr.guesses</div>
          <div class="setting-desc">Maximum number of wrong guesses allowed per round.</div>
          <input
            class="setting-input setting-number"
            type="number" min="1" max="10"
            [(ngModel)]="settings.max_guesses"
            (ngModelChange)="save()"
          />
        </div>
      </div>

      <!-- FILE FILTER section -->
      <div class="settings-section" id="section-filter">
        <div class="section-header">FILE FILTER</div>

        <div class="setting-row">
          <div class="setting-key">codeguessr.minLinesPerFile</div>
          <div class="setting-desc">Minimum number of lines a file must have to be included.</div>
          <input
            class="setting-input setting-number"
            type="number" min="1" max="500"
            [(ngModel)]="settings.min_lines"
            (ngModelChange)="save()"
          />
        </div>

        <div class="setting-row">
          <div class="setting-key">codeguessr.minCharsInLine</div>
          <div class="setting-desc">Minimum non-whitespace characters required in the highlighted line.</div>
          <input
            class="setting-input setting-number"
            type="number" min="0" max="200"
            [(ngModel)]="settings.min_line_chars"
            (ngModelChange)="save()"
          />
        </div>

        <div class="setting-row">
          <div class="setting-key">codeguessr.includePattern</div>
          <div class="setting-desc">Regex pattern — only files whose path matches are included. Leave blank to include all.</div>
          <input
            class="setting-input setting-text"
            type="text" placeholder="e.g. src/.*\\.ts$"
            [(ngModel)]="settings.include_pattern"
            (ngModelChange)="onPatternChange()"
            [class.input-error]="includeError"
          />
          @if (includeError) {
            <div class="regex-error">{{ includeError }}</div>
          }
        </div>

        <div class="setting-row">
          <div class="setting-key">codeguessr.ignorePattern</div>
          <div class="setting-desc">Regex pattern — files whose path matches are excluded.</div>
          <input
            class="setting-input setting-text"
            type="text" placeholder="e.g. \\.test\\."
            [(ngModel)]="settings.ignore_pattern"
            (ngModelChange)="onPatternChange()"
            [class.input-error]="ignoreError"
          />
          @if (ignoreError) {
            <div class="regex-error">{{ ignoreError }}</div>
          }
        </div>
      </div>

      <!-- Start button -->
      <div class="start-row">
        <button
          class="start-btn"
          [disabled]="hasError"
          (click)="startGame()"
        >
          ▶ Start Game
        </button>
      </div>

    </main>
  </div>

  <!-- Status Bar -->
  <footer class="statusbar">
    <div class="sb-left">
      <span class="sb-item">⚡ CodeGuessr</span>
      <span class="sb-sep">|</span>
      <span class="sb-item">Settings</span>
    </div>
    <div class="sb-right">
      <span class="sb-item">UTF-8</span>
    </div>
  </footer>

</div>
  `,
  styles: [`
    * { box-sizing: border-box; margin: 0; padding: 0; }

    .vscode {
      display: flex;
      flex-direction: column;
      height: 100vh;
      background: #1e1e1e;
      color: #cccccc;
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 13px;
    }

    /* Tab bar */
    .tab-bar {
      display: flex;
      background: #2d2d2d;
      border-bottom: 1px solid #252526;
      flex-shrink: 0;
    }
    .tab {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 0 14px;
      height: 35px;
      font-size: 13px;
      color: #969696;
      border-right: 1px solid #252526;
      cursor: pointer;
    }
    .tab-active {
      background: #1e1e1e;
      color: #cccccc;
      border-top: 1px solid #0078d4;
    }
    .tab-icon { width: 14px; height: 14px; opacity: 0.8; }

    /* Breadcrumb */
    .breadcrumb {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 4px 12px;
      background: #1e1e1e;
      border-bottom: 1px solid #2d2d2d;
      font-size: 12px;
      color: #969696;
      flex-shrink: 0;
    }
    .bc-sep { color: #555; }
    .bc-leaf { color: #cccccc; }

    /* Workbench */
    .workbench {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    /* Activity bar */
    .activitybar {
      width: 48px;
      background: #333333;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-top: 8px;
      gap: 4px;
      flex-shrink: 0;
    }
    .ab-item {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      background: none;
      border: none;
      cursor: pointer;
      color: #858585;
    }
    .ab-item svg { width: 22px; height: 22px; }
    .ab-active { color: #cccccc; }

    /* Sidebar */
    .sidebar {
      width: 220px;
      background: #252526;
      border-right: 1px solid #1e1e1e;
      flex-shrink: 0;
      overflow-y: auto;
      padding-top: 8px;
    }
    .sb-title {
      font-size: 11px;
      font-weight: 700;
      color: #bbbbbb;
      padding: 4px 12px 8px;
      letter-spacing: 0.08em;
    }
    .sb-nav { display: flex; flex-direction: column; }
    .sb-nav-item {
      padding: 4px 12px 4px 20px;
      font-size: 13px;
      color: #969696;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .sb-nav-item:hover { background: #2a2d2e; color: #cccccc; }
    .sb-nav-active { color: #cccccc; background: #2a2d2e; }
    .chevron { font-size: 10px; color: #858585; }

    /* Settings content */
    .settings-content {
      flex: 1;
      overflow-y: auto;
      padding: 24px 40px;
    }

    .settings-section {
      margin-bottom: 32px;
    }

    .section-header {
      font-size: 11px;
      font-weight: 700;
      color: #bbbbbb;
      letter-spacing: 0.08em;
      margin-bottom: 4px;
      padding-bottom: 4px;
      border-bottom: 1px solid #3c3c3c;
    }

    .setting-row {
      padding: 12px 0 12px 16px;
      border-bottom: 1px solid #2a2a2a;
    }

    .setting-key {
      font-size: 13px;
      color: #cccccc;
      margin-bottom: 4px;
    }

    .setting-desc {
      font-size: 12px;
      color: #969696;
      margin-bottom: 8px;
      line-height: 1.5;
    }

    .setting-input {
      background: #3c3c3c;
      border: 1px solid #6b6b6b;
      color: #cccccc;
      padding: 4px 8px;
      font-size: 13px;
      font-family: inherit;
      border-radius: 2px;
      outline: none;
    }
    .setting-input:focus {
      border-color: #0078d4;
    }
    .setting-number {
      width: 80px;
    }
    .setting-text {
      width: 320px;
    }
    .input-error {
      border-color: #f48771 !important;
    }
    .regex-error {
      margin-top: 4px;
      font-size: 12px;
      color: #f48771;
    }

    .start-row {
      padding: 24px 0 0 16px;
    }

    .start-btn {
      background: #0078d4;
      color: #ffffff;
      border: none;
      padding: 8px 20px;
      font-size: 13px;
      font-family: inherit;
      border-radius: 2px;
      cursor: pointer;
      letter-spacing: 0.02em;
    }
    .start-btn:hover:not(:disabled) {
      background: #1184db;
    }
    .start-btn:disabled {
      background: #3c3c3c;
      color: #6b6b6b;
      cursor: not-allowed;
    }

    /* Status bar */
    .statusbar {
      height: 22px;
      background: #007acc;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 8px;
      font-size: 12px;
      color: #ffffff;
      flex-shrink: 0;
    }
    .sb-left, .sb-right { display: flex; align-items: center; gap: 6px; }
    .sb-sep { opacity: 0.5; }
  `],
})
export class SettingsComponent implements OnInit {
  private readonly router = inject(Router);

  settings: GameSettings = { ...DEFAULT_SETTINGS };
  includeError = '';
  ignoreError = '';

  ngOnInit(): void {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        this.settings = { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      } catch {
        // Ignore malformed stored settings and fall back to defaults.
      }
    }
    this.validatePatterns();
  }

  get hasError(): boolean {
    return !!this.includeError || !!this.ignoreError;
  }

  save(): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(this.settings));
  }

  onPatternChange(): void {
    this.validatePatterns();
    this.save();
  }

  validatePatterns(): void {
    this.includeError = '';
    this.ignoreError = '';

    const inc = this.settings.include_pattern.trim();
    const ign = this.settings.ignore_pattern.trim();

    if (inc) {
      try {
        new RegExp(inc);
      } catch (e: unknown) {
        this.includeError = e instanceof Error ? e.message : String(e);
      }
    }
    if (ign) {
      try {
        new RegExp(ign);
      } catch (e: unknown) {
        this.ignoreError = e instanceof Error ? e.message : String(e);
      }
    }
  }

  scrollTo(section: string): void {
    const el = document.getElementById(`section-${section}`);
    el?.scrollIntoView({ behavior: 'smooth' });
  }

  startGame(): void {
    if (this.hasError) return;
    this.router.navigate(['/game'], { state: { settings: this.settings } });
  }
}
