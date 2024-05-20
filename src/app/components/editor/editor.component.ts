import { Component, OnInit } from '@angular/core';
import { MonacoEditorModule, NgxEditorModel } from 'ngx-monaco-editor-v2';
import * as monaco from 'monaco-editor';
import { Store } from '@ngrx/store';
import { selectFileSelectionIsLoading, selectSelectedFile, selectState } from '../../state/game.selector';
import { AppState } from '../../state';
import { filter, map, Observable } from 'rxjs';
import { FileItemDetailed } from '../../types/file.types';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-editor',
  standalone: true,
  imports: [CommonModule, MonacoEditorModule, MatProgressSpinnerModule],
  templateUrl: './editor.component.html',
  styleUrl: './editor.component.scss'
})
export class EditorComponent implements OnInit {
  /** Editor Configs */
  editorOptions: monaco.editor.IStandaloneEditorConstructionOptions = {
    theme: 'vs-dark',
    language: 'python',
    readOnly: true,
  };
  
  state$ = this.store.select(selectState)

  fileName$ = this.store.select(selectSelectedFile).pipe(
    filter((file): file is FileItemDetailed => !!file),
    map(file => file.file_name),
  );

  isLoading$ = this.store.select(selectFileSelectionIsLoading);

  protected fileObj$: Observable<FileItemDetailed> = this.store.select(selectSelectedFile).pipe(
    filter((file): file is FileItemDetailed => !!file)
  )
  
  model$: Observable<NgxEditorModel> = this.fileObj$.pipe(
    map((obj) => {
      return {value: obj.contents};
    })
  )

  constructor(private store: Store<AppState>) {}

  ngOnInit(): void {
  }
}
