const getPieces = async (pieces_id) => {
    const params = pieces_id.map(piece_id => (
        "id=" + piece_id
    )).join('&')

    const response = await fetch("http://127.0.0.1:5003/piece?" + params).then(res => res.json())
    
    return response["pieces"]
}

export default getPieces