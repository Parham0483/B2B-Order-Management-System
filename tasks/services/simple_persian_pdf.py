# tasks/services/enhanced_persian_pdf.py - Corrected version
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display
import arabic_reshaper
from django.http import HttpResponse
from django.conf import settings
import os


class EnhancedPersianInvoicePDFGenerator:
    def __init__(self, invoice):
        self.invoice = invoice
        self.order = invoice.order
        self.customer = self.order.customer
        self.persian_font = 'Vazir'

        # Register Persian font
        try:
            font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Vazir.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Vazir', font_path))
        except Exception as e:
            print(f"Font registration error: {e}")
            self.persian_font = 'Helvetica'

    def reshape_persian_text(self, text):
        """Reshape Persian/Arabic text for proper display"""
        if not text:
            return ""
        try:
            reshaped = arabic_reshaper.reshape(str(text))
            return get_display(reshaped)
        except:
            return str(text)

    def format_persian_number(self, number):
        """Convert English numbers to Persian"""
        if not number:
            return ""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'

        number_str = str(number)
        for i, digit in enumerate(english_digits):
            number_str = number_str.replace(digit, persian_digits[i])
        return number_str

    def create_paragraph_style(self, name, **kwargs):
        """Create paragraph style with safe defaults"""
        defaults = {
            'fontName': self.persian_font,
            'fontSize': 11,
            'alignment': 2,  # Right align for Persian
            'rightIndent': 0,
            'leftIndent': 0,
            'spaceAfter': 6,
        }
        defaults.update(kwargs)
        return ParagraphStyle(name, **defaults)

    def add_letterhead(self, elements):
        """Add company letterhead with logo and official information"""
        try:
            # Company Logo and Header
            header_data = [
                [
                    # Logo placeholder - you would add actual logo here
                    "LOGO",
                    self.reshape_persian_text(f"{settings.BUSINESS_NAME}\n{settings.BUSINESS_NAME_EN}")
                ]
            ]

            header_table = Table(header_data, colWidths=[4 * cm, 12 * cm])
            header_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, 0), self.persian_font),
                ('FONTSIZE', (0, 0), (0, 0), 16),
                ('FONTSIZE', (1, 0), (1, 0), 14),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))

            elements.append(header_table)

            # Services banner
            services_style = self.create_paragraph_style(
                'Services',
                fontSize=12,
                alignment=1,
                textColor=colors.white,
                backColor=colors.orange,
                spaceAfter=10
            )

            services_text = f"{settings.BUSINESS_SERVICES} - {settings.BUSINESS_SUBTITLE}"
            elements.append(Paragraph(self.reshape_persian_text(services_text), services_style))

            # Contact Information
            contact_data = [
                [
                    self.reshape_persian_text(f"آدرس: {settings.BUSINESS_ADDRESS}"),
                    self.reshape_persian_text(f"Address: {settings.BUSINESS_ADDRESS_EN}")
                ],
                [
                    self.reshape_persian_text(f"تلفن: {settings.BUSINESS_PHONE}"),
                    f"Tel: {settings.BUSINESS_PHONE_EN}"
                ],
                [
                    self.reshape_persian_text(f"موبایل: {settings.BUSINESS_MOBILE}"),
                    f"Mobile: {settings.BUSINESS_MOBILE_EN}"
                ],
                [
                    f"Email: {settings.BUSINESS_EMAIL}",
                    f"Web: {settings.BUSINESS_WEBSITE}"
                ]
            ]

            contact_table = Table(contact_data, colWidths=[8 * cm, 8 * cm])
            contact_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))

            elements.append(contact_table)
            elements.append(Spacer(1, 20))

        except Exception as e:
            print(f"❌ Letterhead error: {str(e)}")

    def add_invoice_header(self, elements, is_official):
        """Add invoice header"""
        try:
            # Invoice title
            invoice_type = "صورتحساب فروش کالا و خدمات" if is_official else "فاکتور فروش"

            title_style = self.create_paragraph_style(
                'InvoiceTitle',
                fontSize=16,
                alignment=1,
                textColor=colors.darkred if is_official else colors.darkblue,
                spaceBefore=10,
                spaceAfter=15
            )

            elements.append(Paragraph(self.reshape_persian_text(invoice_type), title_style))

            # Invoice info table
            invoice_number = str(self.invoice.invoice_number)
            date_str = self.invoice.issued_at.strftime('%Y/%m/%d')

            info_data = [
                [
                    self.reshape_persian_text("شماره فاکتور:"),
                    invoice_number,
                    self.reshape_persian_text("تاریخ:"),
                    self.format_persian_number(date_str)
                ]
            ]

            info_table = Table(info_data, colWidths=[3 * cm, 4 * cm, 2 * cm, 3 * cm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
                ('BACKGROUND', (2, 0), (2, 0), colors.lightgrey),
            ]))

            elements.append(info_table)
            elements.append(Spacer(1, 15))

        except Exception as e:
            print(f"❌ Invoice header error: {str(e)}")

    def add_customer_info(self, elements, is_official):
        """Add customer information based on invoice type"""
        try:
            if is_official:
                # Official invoice requires detailed customer info
                customer_title_style = self.create_paragraph_style(
                    'CustomerTitle',
                    fontSize=12,
                    alignment=1,
                    backColor=colors.lightgrey,
                    spaceAfter=10
                )

                elements.append(Paragraph(
                    self.reshape_persian_text("مشخصات فروشنده"),
                    customer_title_style
                ))

                # Seller information for official invoice
                seller_data = [
                    [
                        self.reshape_persian_text("نام شخص حقیقی / حقوقی:"),
                        self.reshape_persian_text(settings.BUSINESS_NAME),
                        self.reshape_persian_text("شماره اقتصادی:"),
                        self.format_persian_number(settings.BUSINESS_ECONOMIC_ID)
                    ],
                    [
                        self.reshape_persian_text("شهرستان:"),
                        self.reshape_persian_text("یزد"),
                        self.reshape_persian_text("کد پستی ۱۰ رقمی:"),
                        self.format_persian_number(settings.BUSINESS_POSTAL_CODE)
                    ],
                    [
                        self.reshape_persian_text("شماره ثبت / شماره ملی:"),
                        self.format_persian_number(settings.BUSINESS_NATIONAL_ID),
                        self.reshape_persian_text("شماره تلفن / نمابر:"),
                        self.format_persian_number(settings.BUSINESS_PHONE.replace('-', ''))
                    ]
                ]

                seller_table = Table(seller_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
                seller_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
                ]))

                elements.append(seller_table)
                elements.append(Spacer(1, 10))

                # Buyer information
                elements.append(Paragraph(
                    self.reshape_persian_text("مشخصات خریدار"),
                    customer_title_style
                ))

                buyer_data = [
                    [
                        self.reshape_persian_text("نام:"),
                        self.reshape_persian_text(self.customer.name or ''),
                        self.reshape_persian_text("کد ملی:"),
                        self.format_persian_number(self.customer.national_id or '')
                    ],
                    [
                        self.reshape_persian_text("آدرس:"),
                        self.reshape_persian_text(self.customer.complete_address or ''),
                        "",
                        ""
                    ]
                ]

                buyer_table = Table(buyer_data, colWidths=[2 * cm, 6 * cm, 2 * cm, 6 * cm])
                buyer_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('BACKGROUND', (2, 0), (2, 0), colors.lightgrey),
                    ('SPAN', (1, 1), (3, 1)),  # Merge address cells
                ]))

                elements.append(buyer_table)

            else:
                # Simple customer info for unofficial invoice
                customer_data = [
                    [
                        self.reshape_persian_text("خریدار:"),
                        self.reshape_persian_text(self.customer.name or '')
                    ]
                ]

                customer_table = Table(customer_data, colWidths=[3 * cm, 13 * cm])
                customer_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
                ]))

                elements.append(customer_table)

            elements.append(Spacer(1, 15))

        except Exception as e:
            print(f"❌ Customer info error: {str(e)}")

    def add_items_table(self, elements, is_official):
        """Add items table based on invoice type"""
        try:
            if is_official:
                # Official invoice detailed table
                headers = [
                    "ردیف", "کد کالا", "شرح کالا یا خدمات",
                    "تعداد/مقدار", "واحد", "مبلغ واحد (ریال)",
                    "مبلغ کل (ریال)", "مبلغ تخفیف", "مبلغ کل پس از تخفیف (ریال)",
                    "جمع مالیات و عوارض", "جمع کل مبلغ کالا"
                ]

                col_widths = [1 * cm, 1.5 * cm, 3 * cm, 1.5 * cm, 1 * cm, 2 * cm, 2 * cm, 1.5 * cm, 2 * cm, 2 * cm, 2 * cm]

                # Table data
                table_data = [[self.reshape_persian_text(h) for h in headers]]

                # Add items
                for i, item in enumerate(self.order.items.all(), 1):
                    # Use the correct field names from OrderItem model
                    unit_price = int(item.quoted_unit_price or 0)
                    quantity = int(item.final_quantity or 0)
                    total_price = unit_price * quantity
                    tax_amount = int(total_price * settings.DEFAULT_TAX_RATE) if settings.INCLUDE_TAX_IN_OFFICIAL_INVOICES else 0
                    final_amount = total_price + tax_amount

                    row = [
                        self.format_persian_number(str(i)),
                        self.format_persian_number(str(getattr(item.product, 'sku', i) or i)),
                        self.reshape_persian_text(item.product.name),
                        self.format_persian_number(str(quantity)),
                        self.reshape_persian_text("عدد"),
                        self.format_persian_number(f"{unit_price:,}"),
                        self.format_persian_number(f"{total_price:,}"),
                        self.format_persian_number("0"),
                        self.format_persian_number(f"{total_price:,}"),
                        self.format_persian_number(f"{tax_amount:,}"),
                        self.format_persian_number(f"{final_amount:,}")
                    ]
                    table_data.append(row)

                # Add totals row
                total_amount = sum(int((item.quoted_unit_price or 0) * (item.final_quantity or 0)) for item in self.order.items.all())
                total_tax = int(total_amount * settings.DEFAULT_TAX_RATE) if settings.INCLUDE_TAX_IN_OFFICIAL_INVOICES else 0
                grand_total = total_amount + total_tax

                totals_row = [
                    "", "", self.reshape_persian_text("جمع کل"), "", "", "",
                    self.format_persian_number(f"{total_amount:,}"),
                    self.format_persian_number("0"),
                    self.format_persian_number(f"{total_amount:,}"),
                    self.format_persian_number(f"{total_tax:,}"),
                    self.format_persian_number(f"{grand_total:,}")
                ]
                table_data.append(totals_row)

            else:
                # Simple unofficial invoice table
                headers = ["ردیف", "کالا", "تعداد", "قیمت واحد", "مبلغ کل"]
                col_widths = [2 * cm, 6 * cm, 2 * cm, 3 * cm, 3 * cm]

                table_data = [[self.reshape_persian_text(h) for h in headers]]

                for i, item in enumerate(self.order.items.all(), 1):
                    # Use the correct field names from OrderItem model
                    unit_price = int(item.quoted_unit_price or 0)
                    quantity = int(item.final_quantity or 0)
                    total_price = unit_price * quantity

                    row = [
                        self.format_persian_number(str(i)),
                        self.reshape_persian_text(item.product.name),
                        self.format_persian_number(str(quantity)),
                        self.format_persian_number(f"{unit_price:,}"),
                        self.format_persian_number(f"{total_price:,}")
                    ]
                    table_data.append(row)

            # Create table
            items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

            # Table styling
            style_commands = [
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, -1), 8 if is_official else 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]

            # Highlight totals row if official
            if is_official and len(table_data) > 1:
                style_commands.append(('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey))

            items_table.setStyle(TableStyle(style_commands))
            elements.append(items_table)
            elements.append(Spacer(1, 15))

        except Exception as e:
            print(f"❌ Items table error: {str(e)}")

    def add_totals_section(self, elements, is_official):
        """Add totals section"""
        try:
            if is_official:
                # Official invoice detailed totals
                totals_data = [
                    [
                        self.reshape_persian_text("شرایط و نحوه فروش:"),
                        self.reshape_persian_text("نقدی"),
                        self.reshape_persian_text("غیر نقدی"),
                        ""
                    ],
                    [
                        self.reshape_persian_text("توضیحات:"),
                        "......................................................",
                        "",
                        ""
                    ]
                ]

                totals_table = Table(totals_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
                totals_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('SPAN', (1, 1), (3, 1)),  # Merge description cells
                ]))

                elements.append(totals_table)

            else:
                # Simple total for unofficial invoice
                total_data = [
                    [
                        self.reshape_persian_text("مجموع:"),
                        self.format_persian_number(f"{int(self.invoice.total_amount or 0):,} تومان")
                    ]
                ]

                total_table = Table(total_data, colWidths=[4 * cm, 8 * cm])
                total_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
                ]))

                elements.append(total_table)

            elements.append(Spacer(1, 20))

        except Exception as e:
            print(f"❌ Totals error: {str(e)}")

    def add_signature_section(self, elements):
        """Add signature section"""
        try:
            signature_data = [
                [
                    self.reshape_persian_text("مهر و امضای فروشنده"),
                    self.reshape_persian_text("مهر و امضای خریدار")
                ],
                ["", ""],
                ["", ""]
            ]

            signature_table = Table(signature_data, colWidths=[8 * cm, 8 * cm], rowHeights=[0.8 * cm, 2 * cm, 0.5 * cm])
            signature_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))

            elements.append(signature_table)

        except Exception as e:
            print(f"❌ Signature error: {str(e)}")

    def generate_pdf(self):
        """Generate PDF with comprehensive error handling"""
        try:
            is_official = self.order.business_invoice_type == 'official'

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=1.5 * cm,
                leftMargin=1.5 * cm,
                topMargin=1.5 * cm,
                bottomMargin=1.5 * cm,
                title=f"Invoice-{self.invoice.invoice_number}"
            )

            elements = []

            # Add all sections
            self.add_letterhead(elements)
            self.add_invoice_header(elements, is_official)
            self.add_customer_info(elements, is_official)
            self.add_items_table(elements, is_official)
            self.add_totals_section(elements, is_official)
            self.add_signature_section(elements)

            doc.build(elements)
            return buffer

        except Exception as e:
            print(f"❌ PDF generation error: {str(e)}")
            return self.create_fallback_pdf()

    def create_fallback_pdf(self):
        """Create simple fallback PDF if main generation fails"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        elements = [
            Paragraph(f"Invoice #{self.invoice.invoice_number}",
                      ParagraphStyle('Fallback', fontName='Helvetica-Bold', fontSize=16)),
            Spacer(1, 20),
            Paragraph(f"Customer: {self.customer.name}",
                      ParagraphStyle('Normal', fontName='Helvetica', fontSize=12)),
            Paragraph(f"Total: {self.invoice.total_amount:,.0f} Toman",
                      ParagraphStyle('Normal', fontName='Helvetica', fontSize=12)),
        ]

        doc.build(elements)
        return buffer

    def get_http_response(self):
        """Return HTTP response with PDF"""
        buffer = self.generate_pdf()

        invoice_type = "official" if self.order.business_invoice_type == 'official' else "unofficial"
        filename = f"invoice_{self.invoice.invoice_number}_{invoice_type}.pdf"

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response