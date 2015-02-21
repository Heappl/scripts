#!/usr/bin/python3

def parse_options():
    import optparse, sys

    parser = optparse.OptionParser()
    parser.add_option("-a", "--amount", dest="amount", type="float", help="credited amount to be paid")
    parser.add_option("-m", "--months", dest="months", type="int", help="number of months to calculate installment")
    parser.add_option("-r", "--interest_rate", dest="interest", type="float", help="yearly interests rate (in percent) to be paid")
    parser.add_option("--commission", dest="commission_upfront", default=0.0, type="float", help="one time commission to be paid upfront")
    parser.add_option("--commission_in_loan", dest="commission_in_loan", default=0.0, type="float", help="one time commission to be added to the total credited sum")
    parser.add_option("-i", "--installment", dest="installment", type="float", help="installment that you wish to pay")
    parser.add_option("-f", "--falling", dest="falling", default = False, action = 'store_true', help="falling installment - pay always the same capital")
    (options, _) = parser.parse_args()

    if (not options.amount):
        print("amount must be set")
        sys.exit(1)
    if (not options.interest):
        print("interest_rate must be set")
        sys.exit(1)
    if (not options.months and not options.installment):
        print("nothing to do, set one of options: months or installment")
        sys.exit(1)
    def checkPercent(val, name):
        if ((val < 0.0) or (val > 100.0)):
            print("percent value for " + name + " must be between 0 and 100")
            sys.exit(1)
        return val / 100.0
    options.interest = checkPercent(options.interest, "interest")
    options.commission_upfront = checkPercent(options.commission_upfront, "commission_upfront")
    options.commission_in_loan = checkPercent(options.commission_in_loan, "commission in loan")
    if (options.commission_in_loan and options.commission_upfront):
        print("can't set upfront and in loan commission at the same time")
        sys.exit(1)
    return options

def calculateInstallment(capital, interest, months):
    import math
    monthly = interest / 12.0
    mult = math.exp(monthly * months) / sum([math.exp(monthly * k) for k in range(0, months)])
    return capital * mult

def calculateFallingInstallements(capital, interest, months):
    import math
    monthly = interest / 12.0
    left = capital
    capitalInInstallement = capital / months
    ret = []
    for i in range(0, months):
        ret.append((left * math.exp(monthly) - left) + capitalInInstallement)
        left -= capitalInInstallement
    return ret

def calculateMonths(capital, interest, installment):
    import math
    rate = capital / installment
    monthly = interest / 12.0
    months = 0
    total = 0
    while(total < rate):
        total = total + 1.0 / math.exp(monthly * months)
        months = months + 1
    return months

def calculateCommission(commission):
    return 1.0 / (1.0 - commission) - 1

opts = parse_options()

print("amount to borrow: ", opts.amount)
print("yearly interest rate: ", opts.interest)
print("commission: ", opts.commission_upfront + opts.commission_in_loan)
opts.commission_in_loan = calculateCommission(opts.commission_in_loan)
print("actual commission: ", opts.commission_upfront + opts.commission_in_loan)
opts.amount = opts.amount * (1.0 + opts.commission_in_loan)
print("amount to be credited: ", opts.amount)

if (opts.months):
    installment = calculateInstallment(opts.amount, opts.interest, opts.months)
    print("calculated for desired " + str(opts.months) + " months of paying loan")
    print(" equal installements:")
    print("  installment: ", installment)
    print("  total paid: ", installment * opts.months + opts.commission_upfront)
    if (opts.falling):
        print(" falling installements:")
        installements = calculateFallingInstallements(opts.amount, opts.interest, opts.months)
        i = 1
        total = 0
        for installement in installements:
            print("   paid in " + str(i) + " month: " + str(installement))
            total = total + installement
            i = i + 1
        print("  total paid: ", total)

if (opts.installment):
    months = calculateMonths(opts.amount, opts.interest, opts.installment)
    installment = calculateInstallment(opts.amount, opts.interest, months)
    print("calculated for desired " + str(opts.installment) + " installment")
    print("  desired equal installments of: ", opts.installment)
    print(" smaller installement:")
    print("  months: ", months)
    print("  actual installment: ", installment)
    print("  total paid: ", installment * months + opts.commission_upfront)
    months = max(1, months - 1)
    installment = calculateInstallment(opts.amount, opts.interest, months)
    print(" bigger installement:")
    print("  months: ", months)
    print("  actual installment: ", installment)
    print("  total paid: ", installment * months + opts.commission_upfront)

