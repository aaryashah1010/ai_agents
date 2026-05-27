SAMPLE_DOCUMENTS = {
    "1. Purchase Invoice (ABC Suppliers)": """
    INVOICE - ABC SUPPLIERS INC
    GSTIN: 24ABCDE1234F1Z5
    Bill To: Enterprise Hub Corp
    Invoice No: INV-4587
    Date: 2026-05-15
    
    Items:
    1. Product A | Qty: 10 | Rate: 500 | Total: 5000
    
    Subtotal: 5000
    CGST 9%: 450
    SGST 9%: 450
    Total Amount: 5900
    Terms: Due immediately upon receipt.
    """,

    "2. Sales Invoice (Global Tech)": """
    GLOBAL TECH SOLUTIONS
    GSTIN: 27GTECH9876A1Z2
    Invoice To: Ishti Patel Development Studio
    Invoice Reference: GTS-2026-899
    Date of Issue: 2026-05-20
    Payment Due Deadline: 2026-06-20
    
    Line Details:
    - Cloud Infrastructure Hosting Package | Code: CLD-01 | Qty: 1 | Rate: 12000.00
    - Managed Database Service Addon | Code: DB-SUB | Qty: 2 | Rate: 1500.00 | Total: 3000.00
    
    Net Taxable Subtotal: 15000.00
    Integrated GST (IGST) 18%: 2700.00
    Grand Payable Total: 17700.00
    Payment Condition: Net 30 Days.
    """,

    "3. Purchase Order (Titan Industries)": """
    TITAN INDUSTRIES LTD - PURCHASE ORDER
    PO Number: PO-77412
    Date: 2026-05-18
    To Vendor: Steel Works Manufacturing
    GSTIN: 24STEEL5544K1Z9
    
    We hereby place an order for the following items:
    - Heavy Duty Mild Steel Rods Grade-A | Qty: 50 | Unit: Kg | Unit Price: 120 | Line Total: 6000
    - Industrial Steel Brackets Type-2 | Qty: 100 | Unit: Pcs | Unit Price: 45 | Line Total: 4500
    
    Total Order Valuation: 10500.00
    Please deliver to Warehouse Block C within 7 business days.
    """,

    "4. Sales Order (Nexus Retail)": """
    NEXUS RETAIL APPARELS - SALES ORDER CONFIRMATION
    Order Index Reference: SO-9901
    Date: 2026-05-22
    Client Name: MegaMart Outlets Ltd
    
    Confirmed Items Scheduled for Dispatch:
    - Premium Cotton T-Shirts (Black) | SKU: TS-BLK-M | Qty: 500 | Rate: 180 | Total: 90000
    - Slim Fit Denim Jeans (Blue) | SKU: JN-BLU-32 | Qty: 200 | Rate: 650 | Total: 130000
    
    Subtotal: 220000.00
    Tax Allocation: Standard 5% GST included in base price.
    Total Confirmed Value: 220000.00
    """,

    "5. Commercial Quotation (Solaris Energy)": """
    SOLARIS ENERGY SYSTEMS - PRICE QUOTATION
    Quote Number: QUO-2026-V1
    Valid Until: 2026-06-15
    Prepared For: Green Colonialism Research Institute
    
    Proposed Project Line Estimation Layout:
    - Monocrystalline Solar Panels 450W | Qty: 12 | Rate: 8500 | Total: 102000
    - Hybrid Inverter 5KVA Grid-Tied | Qty: 1 | Rate: 45000 | Total: 45000
    - Structural Aluminum Railing & Cable Kits | Qty: 1 | Rate: 15000 | Total: 15000
    
    Estimated Subtotal: 162000.00
    Estimated Installation Service Charges: 18000.00
    Gross Estimated Budget: 180000.00
    """,

    "6. Delivery Challan (Logistics Pro)": """
    DELIVERY CHALLAN - NON-COMMERCIAL TRANSPORT
    Challan Serial Number: DC-4041
    Date: 2026-05-24
    Dispatched From: Devbhai Electronics Inventory Hub
    Consigned To: Ishti Patel Lab Workshop
    
    Description of Goods Transported under Transit Safeguard:
    - MQ135 Air Quality Sensor Modules | Qty: 5 | Unit: Nos
    - BME280 Environmental Sensor Breakout Boards | Qty: 5 | Unit: Pcs
    - ESP32 NodeMCU Development Microcontrollers | Qty: 10 | Unit: Pcs
    
    Value listed for custom clearance security only: Rs. 4500.00
    Note: Goods sent for prototyping validation project execution. Not for retail sale.
    """,

    "7. Payment Advice (HDFC Corporate Platform)": """
    HDFC BANK - CORPORATE PAYMENT ADVICE SUMMARY
    Transaction Reference ID: TXN-99841257A
    Payment Execution Date: 2026-05-25
    Remitter Account Name: Alpha Consultancies Pvt Ltd
    Beneficiary Account Target: Pal Kaneria Web Services
    
    Settlement Financial Breakdown:
    Settled Amount: Rs. 45000.00
    Bank Remittance Fee: Rs. 0.00
    In Settlement of Invoice Reference: PKWS-MAY-04
    
    Status: Successfully Dispatched via NEFT Network.
    """,

    "8. Corrupted/Messy Receipt (Cafeteria Order)": """
    WELCOME TO CENTRAL BAKERY & CAFE
    2026-05-23 14:22
    STATION ROAD, GANDHINAGAR
    
    2 x Cold Coffee Regular @ 90 = 180
    1 x Paneer Cheese Grilled Sandwich @ 120 = 120
    
    TOTAL AMOUNT DUE: 300.00
    CASH PAID: 500.00
    CHANGE RETURNED: 200.00
    Thank you! Visit again.
    """,

    "9. Purchase Invoice with Missing Fields (Hardware Hub)": """
    HARDWARE HUB DISTRIBUTORS
    Invoice No: HH-8891
    
    Purchased Row Details:
    - Cat6 Ethernet Networking Cable Reel 100m | Qty: 2 | Total Base Price: 7000
    
    Gross Total: 7000.00
    """,

    "10. High-Value Order (Matrix Automation)": """
    MATRIX AUTOMATION LABS - PURCHASE INVOICE
    GSTIN: 24MATRIX8877F1ZM
    Invoice Serial: MAL-9982
    Date: 2026-05-12
    Client: Automation Systems Ltd
    
    Core Project Equipment Items Order Layout:
    - Robotic Arm Pick-and-Place Module V4 | Qty: 2 | Rate: 250000 | Total: 500000
    - Programmable Logic Controller (PLC) Master Unit | Qty: 5 | Rate: 45000 | Total: 225000
    
    Subtotal Net Amount: 725000.00
    Central GST (CGST) 9%: 65250.00
    State GST (SGST) 9%: 65250.00
    Grand Aggregate Invoice Total: 855500.00
    Payment Terms: Net 15 Days from delivery date.
    """
}