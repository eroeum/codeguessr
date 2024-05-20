import { createReducer, on } from '@ngrx/store';
import { FileItem, FileItemChoice, FileItemDetailed } from '../types/file.types';
import { fileContentRequest, fileContentReturned, fileDataReturned, guess, startGame } from './game.actions';

type GameState = 'Setting Up' | 'Game Configuration' | 'Game' | 'Game Finish';

export const FEATURE_KEY = 'GameState'

export interface AppState {
    state: GameState,
    files: FileItem[],
    selectedFile: FileItemDetailed | null,
    fileIsLoading: boolean,
    isGuessCorrect: boolean,
}
export const initialState: AppState = {
    state: 'Setting Up',
    files: [],
    selectedFile: null,
    fileIsLoading: false,
    isGuessCorrect: true,
}


export const gameReducer = createReducer<AppState>(
    initialState,
    on(fileDataReturned, (state, payload) => {
        return {
            ...state,
            files: payload.payload,
            state: 'Game Configuration'
        };
    }),
    on(fileContentRequest, (state) => {
        return {
            ...state,
            selectedFile: null,
            fileIsLoading: true,
        }
    }),
    on(fileContentReturned, (state, payload) => {
        return {
            ...state,
            selectedFile: payload.payload,
            fileIsLoading: false,
        }
    }),
    on(startGame, (state) => {
        return {
            ...state,
            state: 'Game',
        };
    }),
    on(guess, (state, payload) => {
        const actual: FileItem = {
            file_name: state.selectedFile?.file_name || '',
            file_type: state.selectedFile?.file_type || '',
            path: ((state.selectedFile?.path || '') as string).split('/') as any as string[],
        }

        const isCorrect = [
            actual.file_name === payload.guess.file_name,
            actual.path.join('/') === payload.guess.path.join('/'),
        ].every((val) => val)

        return {
            ...state,
            state: 'Game Finish',
            isGuessCorrect: isCorrect,
        }
    })
);
