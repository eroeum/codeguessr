import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { map, Observable } from 'rxjs';
import { FileItem, FileItemDetailed, FileQuery } from '../types/file.types';

@Injectable({
  providedIn: 'root',
})
export class CodeService {
  apiUrl = 'api/v1/code';

  fileFilterForm = new FormGroup({
    include: new FormControl<string>(''),
    exclude: new FormControl<string>(''),
  })

  constructor(private http: HttpClient) { }

  getFiles(): Observable<FileItem[]> {
    return this.http.get<FileQuery[]>(this.apiUrl).pipe(map((queryItems) => {
      return queryItems.map((item) => {
        const path = item.path.length === 0 ? [] : item.path.split('/');
        return {
          file_name: item.file_name,
          file_type: item.file_type,
          path: path,
        }
      })
    }));
  }

  getFileContents(filePath: string): Observable<FileItemDetailed> {
    const uri = `${this.apiUrl}/${filePath}`;
    console.log(uri)
    return this.http.get<FileItemDetailed>(uri);
  }
}
