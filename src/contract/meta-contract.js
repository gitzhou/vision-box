async function ftTransfer({requestId, network, purse, feeb, codehash, genesis, receivers, senderWif, utxoCount}) {
    let result
    try {
        const ft = new metaContract.FtManager({network, purse, feeb,})
        let utxoCountTarget
        if (receivers.length <= 5) {
            utxoCountTarget = 20
        } else if (receivers.length <= 12) {
            utxoCountTarget = 8
        } else {
            utxoCountTarget = 3
        }
        while (utxoCount > utxoCountTarget) {
            await ft.merge({codehash, genesis, ownerWif: senderWif,})
            utxoCount -= 19
        }
        let {txid} = await ft.transfer({codehash, genesis, receivers, senderWif,})
        result = {code: 0, message: 'OK', txid,}
    } catch (e) {
        result = {code: e.code, message: e.message,}
    }
    Bridge.js_callback(JSON.stringify({requestId, result}))
}
