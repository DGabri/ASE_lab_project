import axios from 'axios'

const getPieces = async (access_token, pieces_id) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const params = pieces_id.map(piece_id => (
        "id=" + piece_id
    )).join('&')

    const response = await axiosInstance.get(
        "https://localhost:3000/piece/piece?" + params,
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            }
        }
    )

    if (response.status != 200) {
        throw new Error(response.data.err)  
    }

    return response.data.pieces
}

export default getPieces