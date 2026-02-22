import { Component, DestroyRef, inject, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { HttpErrorResponse } from '@angular/common/http';

import hljs from 'highlight.js/lib/core';
import c from 'highlight.js/lib/languages/c';
import cpp from 'highlight.js/lib/languages/cpp';
import csharp from 'highlight.js/lib/languages/csharp';
import go from 'highlight.js/lib/languages/go';
import java from 'highlight.js/lib/languages/java';
import javascript from 'highlight.js/lib/languages/javascript';
import kotlin from 'highlight.js/lib/languages/kotlin';
import php from 'highlight.js/lib/languages/php';
import python from 'highlight.js/lib/languages/python';
import ruby from 'highlight.js/lib/languages/ruby';
import rust from 'highlight.js/lib/languages/rust';
import swift from 'highlight.js/lib/languages/swift';
import typescript from 'highlight.js/lib/languages/typescript';
import {
  CompletedRound,
  DEFAULT_SETTINGS,
  GameService,
  GameSettings,
  GuessResponse,
  NewGameResponse,
  RoundSummary,
} from './game.service';

hljs.registerLanguage('c', c);
hljs.registerLanguage('cpp', cpp);
hljs.registerLanguage('csharp', csharp);
hljs.registerLanguage('go', go);
hljs.registerLanguage('java', java);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('kotlin', kotlin);
hljs.registerLanguage('php', php);
hljs.registerLanguage('python', python);
hljs.registerLanguage('ruby', ruby);
hljs.registerLanguage('rust', rust);
hljs.registerLanguage('swift', swift);
hljs.registerLanguage('typescript', typescript);

interface RoundPayloadFields {
  round_num?: number;
  code_display?: string;
  highlight_line?: number;
  potential_score?: number;
  guesses_remaining?: number;
  wrong_guesses?: string[];
  language?: string;
}

interface TreeNode {
  name: string;
  fullPath: string;
  isDir: boolean;
  children: TreeNode[];
}

interface FlatRow {
  name: string;
  fullPath: string;
  isDir: boolean;
  depth: number;
}

interface CompletedRoundSummary {
  roundNum: number;
  correct: boolean;
  targetFile: string;
}

@Component({
  selector: 'app-game',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './game.component.html',
  styleUrl: './game.component.css',
})
export class GameComponent implements OnInit {
  private readonly gameService = inject(GameService);
  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly destroyRef = inject(DestroyRef);

  gameId = '';
  files: string[] = [];
  totalRounds = 5;
  totalScore = 0;
  maxGuesses = 6;
  settings: GameSettings = { ...DEFAULT_SETTINGS };
  error = '';

  searchQuery = '';
  fileTree: TreeNode = { name: '', fullPath: '', isDir: true, children: [] };
  collapsedDirs = new Set<string>();

  // Current round display state.
  roundNum = 1;
  codeLines: SafeHtml[] = [];
  language = 'plaintext';
  highlightLine = 0;
  guessesRemaining = 6;
  potentialScore = 1000;
  wrongGuesses = new Set<string>();

  loading = true;
  guessing = false;

  // Round completion overlay.
  roundOver = false;
  gameOver = false;
  completedRoundInfo: CompletedRound | null = null;
  completedRounds: CompletedRoundSummary[] = [];

  private pendingNextRound: RoundPayloadFields | null = null;
  private pendingGameRounds: RoundSummary[] | null = null;

  // Matches lines composed entirely of block characters and whitespace.
  private static readonly OBSCURED_PATTERN = /^[\u2588\s]*$/;

  // Maps file extension to a CSS colour for the file-tree icon.
  private static readonly FILE_COLORS: Record<string, string> = {
    ts: '#3178c6', js: '#f0db4f', py: '#4b8bbe', go: '#00acd7',
    rs: '#dea584', java: '#b07219', kt: '#a97bff', cs: '#178600',
    rb: '#cc342d', swift: '#fa7343', php: '#4f5d95', cpp: '#f34b7d', c: '#9b9b9b',
  };

  ngOnInit(): void {
    const nav = this.router.getCurrentNavigation();
    const state = nav?.extras?.state ?? history.state;
    if (state?.['settings']) {
      this.settings = { ...DEFAULT_SETTINGS, ...state['settings'] };
    }
    this.startNewGame();
  }

  get roundNums(): number[] {
    return Array.from({ length: this.totalRounds }, (_, i) => i + 1);
  }

  startNewGame(): void {
    this.loading = true;
    this.guessing = false;
    this.roundOver = false;
    this.gameOver = false;
    this.wrongGuesses = new Set();
    this.completedRounds = [];
    this.completedRoundInfo = null;
    this.pendingNextRound = null;
    this.pendingGameRounds = null;
    this.totalScore = 0;
    this.searchQuery = '';
    this.collapsedDirs = new Set();

    this.gameService
      .newGame(this.settings)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res: NewGameResponse) => {
          this.gameId = res.game_id;
          this.files = res.files;
          this.totalRounds = res.total_rounds;
          this.maxGuesses = res.max_guesses;
          this.fileTree = this.buildFileTree(res.files);
          this.applyRoundPayload(res);
          this.loading = false;
          this.scrollToHighlight();
        },
        error: (err: HttpErrorResponse) => {
          console.error('Failed to start game:', err);
          this.error = err?.error?.['detail'] ?? 'Failed to start game. Check your settings.';
          this.loading = false;
        },
      });
  }

  guess(filePath: string): void {
    if (this.guessing || this.wrongGuesses.has(filePath) || this.roundOver) return;
    this.guessing = true;

    this.gameService
      .submitGuess(this.gameId, filePath)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (result: GuessResponse) => {
          this.totalScore = result.total_score;

          if (result.round_over) {
            this.completedRoundInfo = result.completed_round!;
            this.completedRounds.push({
              roundNum: this.completedRoundInfo.round_num,
              correct: this.completedRoundInfo.correct,
              targetFile: this.completedRoundInfo.target_file,
            });
            this.roundOver = true;

            if (result.game_over) {
              this.gameOver = true;
              this.pendingGameRounds = result.rounds ?? null;
            } else {
              // Buffer the next round's payload to apply after the overlay is dismissed.
              this.pendingNextRound = {
                round_num: result.round_num,
                code_display: result.code_display,
                highlight_line: result.highlight_line,
                potential_score: result.potential_score,
                guesses_remaining: result.guesses_remaining,
                wrong_guesses: result.wrong_guesses,
                language: result.language,
              };
            }
          } else {
            // Same round continues with an updated code reveal.
            this.applyRoundPayload(result);
          }

          this.guessing = false;
        },
        error: (err: unknown) => {
          console.error('Failed to submit guess:', err);
          this.guessing = false;
        },
      });
  }

  nextRound(): void {
    if (!this.pendingNextRound) return;
    this.applyRoundPayload(this.pendingNextRound);
    this.pendingNextRound = null;
    this.roundOver = false;
    this.completedRoundInfo = null;
    this.scrollToHighlight();
  }

  showResults(): void {
    this.router.navigate(['/results'], {
      state: { rounds: this.pendingGameRounds, totalScore: this.totalScore },
    });
  }

  isRoundCorrect(n: number): boolean {
    return this.completedRounds.some(r => r.roundNum === n && r.correct);
  }

  isRoundFailed(n: number): boolean {
    return this.completedRounds.some(r => r.roundNum === n && !r.correct);
  }

  isRoundCompleted(n: number): boolean {
    return this.completedRounds.some(r => r.roundNum === n);
  }

  getTabTitle(n: number): string {
    const completed = this.completedRounds.find(r => r.roundNum === n);
    if (completed) return this.getBaseName(completed.targetFile);
    return `round_${n}.??`;
  }

  isWrong(file: string): boolean {
    return this.wrongGuesses.has(file);
  }

  getExt(path: string): string {
    const name = path.split('/').pop() ?? '';
    const dot = name.lastIndexOf('.');
    return dot >= 0 ? name.slice(dot + 1).toLowerCase() : '';
  }

  getBaseName(path: string): string {
    return path.split('/').pop() ?? path;
  }

  getDirName(path: string): string {
    const parts = path.split('/');
    return parts.length > 1 ? parts.slice(0, -1).join('/') : '';
  }

  getFileColor(ext: string): string {
    return GameComponent.FILE_COLORS[ext] ?? '#858585';
  }

  // ── File tree ────────────────────────────────────────────────────────────

  get visibleRows(): FlatRow[] {
    const query = this.searchQuery.trim().toLowerCase();
    if (query) {
      return this.files
        .filter(f => f.toLowerCase().includes(query))
        .map(f => ({ name: this.getBaseName(f), fullPath: f, isDir: false, depth: 0 }));
    }
    return this.flattenTree(this.fileTree);
  }

  buildFileTree(files: string[]): TreeNode {
    const root: TreeNode = { name: '', fullPath: '', isDir: true, children: [] };
    for (const file of files) {
      const parts = file.split('/');
      let node = root;
      let curPath = '';
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        curPath = curPath ? `${curPath}/${part}` : part;
        const isFile = i === parts.length - 1;
        let child = node.children.find(c => c.name === part);
        if (!child) {
          child = { name: part, fullPath: curPath, isDir: !isFile, children: [] };
          node.children.push(child);
        }
        if (!isFile) node = child;
      }
    }
    this.sortTree(root);
    return root;
  }

  toggleDir(path: string): void {
    const next = new Set(this.collapsedDirs);
    if (next.has(path)) {
      next.delete(path);
    } else {
      next.add(path);
    }
    this.collapsedDirs = next;
  }

  collapseAll(): void {
    const dirs = new Set<string>();
    const collect = (node: TreeNode): void => {
      for (const child of node.children) {
        if (child.isDir) {
          dirs.add(child.fullPath);
          collect(child);
        }
      }
    };
    collect(this.fileTree);
    this.collapsedDirs = dirs;
  }

  onSearch(event: Event): void {
    this.searchQuery = (event.target as HTMLInputElement).value;
  }

  // ── Private helpers ──────────────────────────────────────────────────────

  private applyRoundPayload(payload: RoundPayloadFields): void {
    if (payload.round_num !== undefined) this.roundNum = payload.round_num;
    if (payload.language !== undefined) this.language = payload.language;
    if (payload.code_display !== undefined) {
      this.codeLines = this.highlightLines(payload.code_display, this.language);
    }
    if (payload.highlight_line !== undefined) this.highlightLine = payload.highlight_line;
    if (payload.potential_score !== undefined) this.potentialScore = payload.potential_score;
    if (payload.guesses_remaining !== undefined) this.guessesRemaining = payload.guesses_remaining;
    if (payload.wrong_guesses !== undefined) this.wrongGuesses = new Set(payload.wrong_guesses);
  }

  private highlightLines(code: string, language: string): SafeHtml[] {
    return code.split('\n').map(line => {
      if (GameComponent.OBSCURED_PATTERN.test(line)) {
        return this.sanitizer.bypassSecurityTrustHtml(this.escapeHtml(line));
      }
      try {
        const html = hljs.highlight(line, { language, ignoreIllegals: true }).value;
        return this.sanitizer.bypassSecurityTrustHtml(html);
      } catch {
        return this.sanitizer.bypassSecurityTrustHtml(this.escapeHtml(line));
      }
    });
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  private scrollToHighlight(): void {
    setTimeout(() => {
      const el = document.querySelector('.code-line.highlighted');
      el?.scrollIntoView({ block: 'center', behavior: 'instant' });
    }, 50);
  }

  private sortTree(node: TreeNode): void {
    node.children.sort((a, b) => {
      if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    for (const child of node.children) {
      if (child.isDir) this.sortTree(child);
    }
  }

  private flattenTree(node: TreeNode, depth = 0): FlatRow[] {
    const rows: FlatRow[] = [];
    for (const child of node.children) {
      rows.push({ name: child.name, fullPath: child.fullPath, isDir: child.isDir, depth });
      if (child.isDir && !this.collapsedDirs.has(child.fullPath)) {
        rows.push(...this.flattenTree(child, depth + 1));
      }
    }
    return rows;
  }
}
