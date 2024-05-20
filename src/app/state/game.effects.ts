import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { catchError, EMPTY, exhaustMap, map, withLatestFrom } from 'rxjs';
import { AppState } from '.';
import { CodeService } from '../services/code.service';
import { fileContentRequest, fileContentReturned, fileDataRequest, fileDataReturned, guess, startGame } from './game.actions';
import * as globToRegexp from 'glob-to-regexp';

@Injectable()
export class GameEffects {
    constructor(
        private actions$: Actions,
        private store: Store<AppState>,
        private codeService: CodeService,
    ) {}

    loadFiles$ = createEffect(() => this.actions$.pipe(
        ofType(fileDataRequest),
        exhaustMap(() => this.codeService.getFiles().pipe(
            map(files => {
                return fileDataReturned({ payload: files })
            }),
            // map(files => ({ type: fileDataReturned, payload: files })),
            catchError(() => EMPTY)
        ))
    ));

    loadFileContents$ = createEffect(() => this.actions$.pipe(
        ofType(fileContentRequest),
        exhaustMap((data) => this.codeService.getFileContents(data.path).pipe(
            map(fileContents => fileContentReturned({ payload: fileContents }))
        ))
    ));

    reloadFileContents$ = createEffect(() => this.actions$.pipe(
        ofType(guess),
        withLatestFrom(this.store),
        exhaustMap(([_, state]) => {
            const path: string = state.GameState.selectedFile?.path as any as string || '' as string;
            const fileName = state.GameState.selectedFile?.file_name || '';
            const filePath = path ? `${path}/${fileName}` : fileName;
            return this.codeService.getFileContents(filePath).pipe(
                map(fileContents => fileContentReturned({ payload: fileContents }))
            )
        })
    ))

    loadGameFile$ = createEffect(() => this.actions$.pipe(
        ofType(startGame),
        withLatestFrom(this.store),
        exhaustMap(([payload, state]) => {
            let filtered = [...state.GameState.files];
            let reInclude = globToRegexp.default(payload.payload.include);
            let reExclude = globToRegexp.default(payload.payload.exclude);

            // Handle includes
            if (payload.payload.include) {
                filtered = filtered.filter((file) => {
                    const path = file.path.length ? `${file.path.join('/')}/${file.file_name}` : file.file_name;
                    return reInclude.test(path);
                })
            }

            // Handle Excludes
            if (payload.payload.exclude) {
                filtered = filtered.filter((file) => {
                    const path = file.path.length ? `${file.path.join('/')}/${file.file_name}` : file.file_name;
                    return !reExclude.test(path);
                })
            }

            // Choose file
            const gameFile = filtered[Math.floor(Math.random() * filtered.length)];
            const gamePath = gameFile.path.length ? `${gameFile.path.join('/')}/${gameFile.file_name}` : gameFile.file_name;

            return this.codeService.getFileContents(gamePath).pipe(
                map(fileContents => {
                    let lines = fileContents.contents.split('\n');

                    // Choose a random line and choose the next 10 lines
                    const snippetLength = 10;
                    const startLine = Math.floor(Math.random() * Math.max(0, lines.length - snippetLength));
                    const endLine = startLine + snippetLength;

                    lines = lines.map((line, index) => {
                        if (index >= startLine && index <= endLine) {
                            return line;
                        }
                        return line.replace(/\S/g, '*');
                    })

                    


                    return fileContentReturned({ payload: {...fileContents, contents: lines.join('\n')} })
                })
            )
        })
    ))
}
