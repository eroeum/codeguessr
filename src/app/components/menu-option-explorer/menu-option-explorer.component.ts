import { Component, forwardRef, Input, OnInit } from '@angular/core';
import { MenuOption } from '../menu-bar/menu-bar';
import {MatTreeModule, MatTreeNestedDataSource} from '@angular/material/tree';
import { NestedTreeControl } from '@angular/cdk/tree';
import {MatIconModule} from '@angular/material/icon';
import {MatButtonModule} from '@angular/material/button';
import { Store } from '@ngrx/store';
import { AppState } from '../../state';
import { selectFiles } from '../../state/game.selector';
import { FileItem } from '../../types/file.types';
import { CodeService } from '../../services/code.service';
import { combineLatest, startWith } from 'rxjs';
import { fileContentRequest, startGame } from '../../state/game.actions';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import {MatDividerModule} from '@angular/material/divider';
import {
  MatFormFieldModule,
} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import * as globToRegexp from 'glob-to-regexp';


class MenuOptionExplorer extends MenuOption {
  tabIcon = 'file_copy';
  name ='game setup';
}

interface FileItemNode {
  name: string,
  obj?: FileItem,
  children: FileItemNode[],
}

@Component({
  selector: 'app-menu-option-explorer',
  standalone: true,
  imports: [
    MatTreeModule,
    MatIconModule,
    MatButtonModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatDividerModule,
  ],
  templateUrl: './menu-option-explorer.component.html',
  styleUrl: './menu-option-explorer.component.scss',
  providers: [{ provide: MenuOption, useValue: forwardRef(() => new MenuOptionExplorer()) }]
})
export class MenuOptionExplorerComponent implements OnInit {
  constructor(private store: Store<AppState>, private codeService: CodeService) {}

  treeControl = new NestedTreeControl<FileItemNode>(node => node.children);
  dataSource = new MatTreeNestedDataSource<FileItemNode>();

  fileFilterForm = this.codeService.fileFilterForm;

  @Input() selected: FileItemNode | null = null;

  ngOnInit(): void {
      combineLatest([
        this.store.select(selectFiles),
        this.fileFilterForm.valueChanges.pipe(
          startWith({
            include: '',
            exclude: '',
          })
        ),
      ]).subscribe(([files, filter]) => {
        const dataSource: FileItemNode[] = []
        files.forEach((file) => {
          let source: FileItemNode[] = dataSource;

          let filePath = file.path.length ? `${file.path.join('/')}/${file.file_name}` : file.file_name;
          
          // Handle include filter
          if (filter.include) {
            let re = globToRegexp.default(filter.include);
            if (!re.test(filePath)) {
              return;
            }
          }

          // Handle exclude filter
          if (filter.exclude) {
            let re = globToRegexp.default(filter.exclude);
            if (re.test(filePath)) {
              return;
            }
          }

          // Build all the parents
          file.path.forEach((path) => {

            let index = source.findIndex((item) => item.name === path)
            if (index < 0) {
              let newSource: FileItemNode = {
                name: path,
                children: [],
              };
              source.push(newSource);
              index = source.length - 1;
            }
            source = source[index].children;
          });

          // Build the end node.
          source.push({
            name: file.file_name,
            obj: file,
            children: [],
          });
        });

        this.dataSource.data = dataSource;
      })
  }

  hasChild(_: number, node: FileItemNode) {
    return !!node.children && node.children.length > 0;
  }

  selectFile(node: FileItemNode) {
    this.selected = node;
    if (!node.obj) {
      return;
    }
    const relativePath = node.obj.path.length ?
      `${node.obj.path.join('/')}/${node.name}`:
      node.name;

    this.store.dispatch(fileContentRequest({ path: relativePath }));
  }

  startGame() {
    this.store.dispatch(startGame({ payload: {
      include: this.fileFilterForm.get('include')?.value || '',
      exclude: this.fileFilterForm.get('exclude')?.value || '',
    }}))
  }
}
