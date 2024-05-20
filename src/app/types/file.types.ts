/** Defines the file object. */

/** Defines the query definition from the Files API. */
export interface FileQuery {
    file_name: string,
    file_type: string,
    path: string,
}

/** Defines a file item. */
export interface FileItem {
    file_name: string,
    file_type: string,
    path: string[],
}

/** Defines a file item. */
export interface FileItemDetailed extends FileItem {
    contents: string,
}

export interface FileItemChoice extends FileItemDetailed {
    startLine: number,
    endLine: number,
}
