import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { OcrIntegrationComponent } from './ocr-integration.component';
import { OcrService } from './services/ocr.service';
import { MaterialModule } from 'src/app/material.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

@NgModule({
    declarations: [OcrIntegrationComponent],
    imports: [
        CommonModule,
        MaterialModule,
        FormsModule,
        ReactiveFormsModule,
        HttpClientModule
    ],
    providers: [OcrService],
    exports: [OcrIntegrationComponent]
})
export class OcrIntegrationModule { }
