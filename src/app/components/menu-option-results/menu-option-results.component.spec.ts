import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MenuOptionResultsComponent } from './menu-option-results.component';

describe('MenuOptionResultsComponent', () => {
  let component: MenuOptionResultsComponent;
  let fixture: ComponentFixture<MenuOptionResultsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MenuOptionResultsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(MenuOptionResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
