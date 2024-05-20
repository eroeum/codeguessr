import { createAction, props } from '@ngrx/store';
import { FileItem, FileItemDetailed } from '../types/file.types';

export const fileDataRequest = createAction(
    '[Game Engine] File data requested',
)

export const fileDataReturned = createAction(
    '[Game Engine] File data returned',
    props<{ payload: FileItem[] }>()
);

export const fileContentRequest = createAction(
    '[Game Engine] File contents requested',
    props<{ path: string}>()
)

export const fileContentReturned = createAction(
    '[Game Engine] File contents returned',
    props<{ payload: FileItemDetailed }>()
);

export const startGame = createAction(
    '[Game Engine] Start Game',
    props<{ payload: {include: string, exclude: string} }>()
);

export const guess = createAction(
    '[Game Engine] Guess',
    props<{ guess: FileItem }>()
)
