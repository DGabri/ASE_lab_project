const getRunningAuctions = async (piece_id = null) => {
    const response = await fetch("http://127.0.0.1:5005/auction/running" + (piece_id ? `/${piece_id}` : "")).then(res => res.json())
    return response
}

export default getRunningAuctions