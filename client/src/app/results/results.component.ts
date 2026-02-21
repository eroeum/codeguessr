import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { RoundSummary } from '../game/game.service';

interface GameResult {
  rounds: RoundSummary[];
  totalScore: number;
}

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [],
  templateUrl: './results.component.html',
  styles: [`
    :host { display: block; height: 100vh; overflow: hidden; }

    .vscode {
      display: flex; flex-direction: column;
      height: 100vh; overflow: hidden;
      background: #1e1e1e; color: #cccccc; font-size: 13px;
    }
    .titlebar {
      height: 30px; flex-shrink: 0; background: #3c3c3c;
      display: flex; align-items: center; padding: 0 12px;
      user-select: none; border-bottom: 1px solid #252526;
    }
    .traffic-lights { display: flex; gap: 7px; margin-right: 12px; }
    .tl { width: 12px; height: 12px; border-radius: 50%; }
    .tl.red { background: #ff5f57; }
    .tl.yellow { background: #febc2e; }
    .tl.green { background: #28c840; }
    .titlebar-text { flex: 1; text-align: center; font-size: 13px; color: #cccccc; }

    .workbench { flex: 1; display: flex; overflow: hidden; }

    .activitybar {
      width: 48px; flex-shrink: 0; background: #333333;
      display: flex; flex-direction: column; align-items: center;
      padding-top: 4px; border-right: 1px solid #2b2b2b;
    }
    .ab-item {
      width: 48px; height: 48px; display: flex; align-items: center;
      justify-content: center; background: none; border: none;
      border-left: 2px solid transparent; color: #858585; padding: 0;
    }
    .ab-active { color: #cccccc; border-left-color: #cccccc; }
    .ab-item svg { width: 22px; height: 22px; }

    .editor-group {
      flex: 1; display: flex; flex-direction: column;
      overflow: hidden; background: #1e1e1e; min-width: 0;
    }

    .tabs {
      height: 35px; flex-shrink: 0; background: #2d2d2d;
      display: flex; align-items: stretch; border-bottom: 1px solid #252526;
    }
    .tab {
      display: flex; align-items: center; gap: 6px; padding: 0 12px;
      font-size: 13px; color: #8c8c8c; background: #2d2d2d;
      border-right: 1px solid #252526; white-space: nowrap; min-width: 100px;
    }
    .tab-active {
      background: #1e1e1e; color: #cccccc;
      border-top: 1px solid #007acc; border-bottom: 1px solid #1e1e1e; margin-bottom: -1px;
    }
    .tab-file-icon { width: 13px; height: 13px; flex-shrink: 0; }
    .tab-close { font-size: 11px; color: #858585; margin-left: 6px; }

    .breadcrumb {
      height: 22px; flex-shrink: 0; background: #1e1e1e;
      display: flex; align-items: center; padding: 0 12px; gap: 2px;
      font-size: 12px; border-bottom: 1px solid #454545;
    }
    .bc-item { color: #cccccc; }
    .bc-leaf { font-weight: 500; }
    .bc-sep  { color: #858585; padding: 0 2px; }

    .editor-body { flex: 1; overflow: auto; display: flex; justify-content: center; }

    .result-doc {
      max-width: 680px; width: 100%;
      padding: 48px 40px;
      display: flex; flex-direction: column; gap: 28px;
    }

    .total-score-box {
      display: flex; align-items: baseline; gap: 10px;
      padding: 20px 24px; border-radius: 4px;
      background: rgba(0, 122, 204, 0.08); border-left: 4px solid #007acc;
    }
    .ts-label {
      font-size: 12px; color: #858585;
      text-transform: uppercase; letter-spacing: 0.06em;
    }
    .ts-value {
      font-size: 2.4rem; font-weight: 700; color: #dcdcaa;
      font-variant-numeric: tabular-nums;
    }
    .ts-pts { font-size: 14px; color: #858585; }

    .rounds-table { border-collapse: collapse; width: 100%; }
    .rounds-table th {
      font-size: 11px; color: #858585;
      text-transform: uppercase; letter-spacing: 0.06em;
      padding: 6px 12px 6px 0; text-align: left;
      border-bottom: 1px solid #454545;
    }
    .rounds-table td {
      font-size: 13px; color: #d4d4d4;
      padding: 10px 12px 10px 0; border-bottom: 1px solid #2d2d2d;
      vertical-align: top;
    }
    .rounds-table th:last-child,
    .rounds-table td:last-child { text-align: right; padding-right: 0; }

    .rn-num { color: #858585; font-size: 12px; }

    .filepath {
      font-family: 'Cascadia Code', 'JetBrains Mono', Consolas, monospace;
      font-size: 12px; color: #ce9178; word-break: break-all;
    }

    .verdict-cell { font-size: 14px; font-weight: 700; white-space: nowrap; }
    .verdict-cell.correct { color: #4ec994; }
    .verdict-cell.failed  { color: #f44747; }

    .pts-cell { font-size: 14px; font-weight: 700; color: #858585; white-space: nowrap; }
    .pts-cell.nonzero { color: #dcdcaa; }

    .play-btn {
      align-self: flex-start;
      background: #0e639c; color: #fff; border: none;
      padding: 7px 20px; border-radius: 2px; font-size: 13px;
      letter-spacing: 0.02em; cursor: pointer;
    }
    .play-btn:hover { background: #1177bb; }

    .statusbar {
      height: 22px; flex-shrink: 0; background: #007acc;
      display: flex; align-items: center; justify-content: space-between; padding: 0 6px;
    }
    .sb-left, .sb-right { display: flex; align-items: center; }
    .sb-item { padding: 0 6px; font-size: 12px; color: #fff; white-space: nowrap; border-radius: 2px; }
    .sb-item:hover { background: rgba(255,255,255,0.12); }
  `],
})
export class ResultsComponent implements OnInit {
  private readonly router = inject(Router);

  result: GameResult | null = null;

  ngOnInit(): void {
    const nav = this.router.getCurrentNavigation();
    const state = (nav?.extras?.state ?? history.state) as {
      rounds?: RoundSummary[];
      totalScore?: number;
    };

    if (!state?.rounds || state.totalScore === undefined) {
      this.router.navigate(['/']);
      return;
    }

    this.result = { rounds: state.rounds, totalScore: state.totalScore };
  }

  playAgain(): void {
    this.router.navigate(['/']);
  }
}
